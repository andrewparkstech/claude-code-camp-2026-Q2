#!/usr/bin/env python3
"""Send one command to a running mud_daemon.py session and print whatever
new game text arrives in response.

Waits for the output log to go quiet (no new bytes for --quiet-period
seconds) before returning, since MUD responses can arrive in more than one
network chunk. Falls back to returning whatever has arrived after
--max-wait seconds, so a command that produces no visible output (or a
laggy server) doesn't hang the caller forever.
"""

import argparse
import os
import sys
import time


def default_session_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", help='Command to send, e.g. "look", "north", "kill rat"')
    parser.add_argument("--session-dir", default=default_session_dir())
    parser.add_argument("--quiet-period", type=float, default=0.6)
    parser.add_argument("--max-wait", type=float, default=6.0)
    args = parser.parse_args()

    fifo_path = os.path.join(args.session_dir, "commands.fifo")
    log_path = os.path.join(args.session_dir, "output.log")
    pid_path = os.path.join(args.session_dir, "daemon.pid")

    if not os.path.exists(pid_path):
        status_path = os.path.join(args.session_dir, "status")
        detail = ""
        if os.path.exists(status_path):
            detail = f" Last status: {open(status_path).read().strip()}"
        print(f"No active MUD session in {args.session_dir}. "
              f"Start one with mud_daemon.py first.{detail}", file=sys.stderr)
        sys.exit(1)

    start_offset = os.path.getsize(log_path) if os.path.exists(log_path) else 0

    with open(fifo_path, "w") as f:
        f.write(args.command + "\n")

    deadline = time.time() + args.max_wait
    last_size = start_offset
    last_change = time.time()
    while time.time() < deadline:
        time.sleep(0.15)
        size = os.path.getsize(log_path)
        if size != last_size:
            last_size = size
            last_change = time.time()
        elif size > start_offset and time.time() - last_change >= args.quiet_period:
            break

    with open(log_path, "rb") as f:
        f.seek(start_offset)
        new_data = f.read()

    sys.stdout.buffer.write(new_data)


if __name__ == "__main__":
    main()
