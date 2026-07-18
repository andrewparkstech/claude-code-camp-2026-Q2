#!/usr/bin/env python3
"""Cleanly end a mud_daemon.py session: sends 'quit' through the game (so
the character logs out properly rather than going linkless) and waits for
the daemon to exit. Falls back to SIGTERM if it doesn't exit on its own.
"""

import argparse
import os
import signal
import sys
import time


def default_session_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-dir", default=default_session_dir())
    args = parser.parse_args()

    fifo_path = os.path.join(args.session_dir, "commands.fifo")
    pid_path = os.path.join(args.session_dir, "daemon.pid")

    if not os.path.exists(pid_path):
        print("No active MUD session.")
        return

    with open(pid_path) as f:
        pid = int(f.read().strip())

    try:
        with open(fifo_path, "w") as f:
            f.write("__QUIT__\n")
    except OSError as e:
        print(f"Could not signal the daemon via FIFO ({e}); force-killing.", file=sys.stderr)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return

    for _ in range(20):
        if not os.path.exists(pid_path):
            print("Session stopped cleanly.")
            return
        time.sleep(0.3)

    try:
        os.kill(pid, signal.SIGTERM)
        print("Session did not stop on its own; force-stopped.")
    except ProcessLookupError:
        print("Session stopped.")


if __name__ == "__main__":
    main()
