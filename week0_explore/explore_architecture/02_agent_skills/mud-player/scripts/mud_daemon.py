#!/usr/bin/env python3
"""Persistent connection daemon for a tbaMUD/CircleMUD server.

Owns the raw telnet socket for the whole play session, handles the login
handshake once, and then bridges between a FIFO (for outgoing commands)
and a log file (for incoming game text, with telnet/ANSI control bytes
stripped). Run this once in the background per session; talk to it with
mud_cmd.py and end it with mud_stop.py.

A persistent connection matters here: reconnecting for every command would
repeatedly trigger the login/menu sequence and would leave the character
"linkless" between commands, which in CircleMUD-derived games does not
pause combat -- a linkless character can still be attacked.
"""

import argparse
import os
import re
import select
import signal
import socket
import sys
import time

ANSI_RE = re.compile(rb"\x1b\[[0-9;]*[a-zA-Z]")
IAC = 0xFF


def strip_telnet(data: bytes) -> bytes:
    out = bytearray()
    i, n = 0, len(data)
    while i < n:
        b = data[i]
        if b == IAC and i + 1 < n:
            cmd = data[i + 1]
            if cmd in (0xFB, 0xFC, 0xFD, 0xFE) and i + 2 < n:  # WILL/WONT/DO/DONT
                i += 3
                continue
            if cmd == 0xFA:  # subnegotiation, skip to IAC SE
                j = data.find(bytes([IAC, 0xF0]), i)
                i = (j + 2) if j != -1 else n
                continue
            i += 2
            continue
        out.append(b)
        i += 1
    return bytes(out)


def clean(data: bytes) -> bytes:
    return ANSI_RE.sub(b"", strip_telnet(data))


def recv_available(sock, timeout=0.3) -> bytes:
    sock.settimeout(timeout)
    chunks = []
    try:
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
    except socket.timeout:
        pass
    return b"".join(chunks)


def wait_for(sock, patterns, timeout=8.0):
    """Poll until one of the regex patterns appears in the accumulated
    buffer, or timeout. Returns (matched_pattern_or_None, raw_buffer)."""
    deadline = time.time() + timeout
    buf = b""
    while time.time() < deadline:
        buf += recv_available(sock, timeout=0.3)
        for pat in patterns:
            if re.search(pat, buf):
                return pat, buf
    return None, buf


def default_session_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=4000)
    parser.add_argument("--username", default="dummy")
    parser.add_argument("--password", default="helloworld")
    parser.add_argument("--session-dir", default=default_session_dir())
    args = parser.parse_args()

    session_dir = args.session_dir
    os.makedirs(session_dir, exist_ok=True)
    fifo_path = os.path.join(session_dir, "commands.fifo")
    log_path = os.path.join(session_dir, "output.log")
    pid_path = os.path.join(session_dir, "daemon.pid")
    status_path = os.path.join(session_dir, "status")

    if os.path.exists(pid_path):
        print(f"A session already appears active ({pid_path} exists). "
              f"Stop it with mud_stop.py first.", file=sys.stderr)
        sys.exit(1)

    # Claim the session immediately so concurrent starts are rejected.
    with open(pid_path, "w") as f:
        f.write(str(os.getpid()))
    with open(status_path, "w") as f:
        f.write("connecting\n")

    # Fresh log for this session.
    open(log_path, "wb").close()
    log_f = open(log_path, "ab", buffering=0)

    def emit(data: bytes):
        if data:
            log_f.write(clean(data))

    def fail(msg: str):
        with open(status_path, "w") as f:
            f.write(f"error: {msg}\n")
        if os.path.exists(pid_path):
            os.remove(pid_path)
        sys.exit(1)

    try:
        sock = socket.create_connection((args.host, args.port), timeout=10)
    except OSError as e:
        fail(f"could not connect to {args.host}:{args.port}: {e}")
        return

    try:
        _, buf = wait_for(sock, [rb"[Nn]ame"], timeout=8.0)
        emit(buf)
        if not buf:
            fail("no banner/name prompt received from server")
            return
        sock.sendall(args.username.encode() + b"\r\n")

        pat, buf = wait_for(sock, [rb"Password"], timeout=8.0)
        emit(buf)
        if pat is None:
            fail("never saw a Password prompt after sending username")
            return
        sock.sendall(args.password.encode() + b"\r\n")

        # A fresh login (not reconnecting to an already-linked character)
        # shows one or more MOTD/paging screens ("*** PRESS RETURN...")
        # before the character menu. Keep pressing return through them.
        menu_or_prompt = [rb"Make your choice", rb"\d+H \d+M \d+V"]
        pager = rb"PRESS RETURN|\[Continue|MORE"
        entered = False
        for _ in range(10):
            pat, buf = wait_for(sock, menu_or_prompt + [pager], timeout=8.0)
            emit(buf)
            if pat is None:
                fail("login stalled: never reached the character menu, an "
                     "in-game prompt, or a page-continue marker (wrong "
                     "password, or a full character-creation flow for a "
                     "brand-new name)")
                return
            if pat == rb"Make your choice":
                sock.sendall(b"1\r\n")  # "Enter the game"
                pat, buf = wait_for(sock, [rb"\d+H \d+M \d+V"], timeout=8.0)
                emit(buf)
                if pat is None:
                    fail("selected 'enter the game' but never saw an in-game prompt")
                    return
                entered = True
                break
            if pat == rb"\d+H \d+M \d+V":
                entered = True
                break
            sock.sendall(b"\r\n")  # advance past the pager screen
        if not entered:
            fail("too many MOTD/pager screens; login did not complete")
            return
    except Exception as e:  # noqa: BLE001 - report any failure to the status file
        fail(f"unexpected error during login: {e}")
        return

    with open(status_path, "w") as f:
        f.write("ready\n")

    if not os.path.exists(fifo_path):
        os.mkfifo(fifo_path)
    # Open read-write (not read-only) so the fd never sees a spurious EOF
    # when no writer is currently attached -- a standard FIFO idiom.
    fifo_fd = os.open(fifo_path, os.O_RDWR | os.O_NONBLOCK)

    def handle_stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, handle_stop)

    try:
        while True:
            readable, _, _ = select.select([sock, fifo_fd], [], [], 1.0)
            if sock in readable:
                chunk = recv_available(sock, timeout=0.1)
                if not chunk:
                    emit(b"\r\n[connection closed by server]\r\n")
                    break
                emit(chunk)
            if fifo_fd in readable:
                raw = os.read(fifo_fd, 4096)
                for line in raw.decode(errors="replace").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if line == "__QUIT__":
                        sock.sendall(b"quit\r\n")
                        emit(recv_available(sock, timeout=1.5))
                        raise SystemExit(0)
                    sock.sendall(line.encode() + b"\r\n")
    except SystemExit:
        pass
    finally:
        os.close(fifo_fd)
        sock.close()
        log_f.close()
        with open(status_path, "w") as f:
            f.write("stopped\n")
        if os.path.exists(pid_path):
            os.remove(pid_path)


if __name__ == "__main__":
    main()
