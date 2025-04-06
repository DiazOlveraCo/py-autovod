#!/usr/bin/env python3

import os
import sys
import argparse
from settings import config
from stream_manager import StreamManager

def main():
    version = config.get("general", "version", fallback="1.0.0")

    print(f"Starting AutoVOD v{version}")

    parser = argparse.ArgumentParser(
        description="AutoVOD - Automatic VOD downloader for Twitch, Kick, and YouTube"
    )

    parser.add_argument("-n", "--name", help="Single streamer name to monitor")
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Display the current version",
    )
    args = parser.parse_args()

    if not os.path.exists("recordings"):
        try:
            os.mkdir("recordings")
        except:
            pass

    # Display version and exit
    if args.version:
        print(f"Version: {version}")
        return

    manager = StreamManager()

    if args.name:
        manager.start(args.name)
    else:
        manager.start()

    manager.wait()


if __name__ == "__main__":
    assert sys.version_info >= (3, 9), "Python 3.9 or higher is required"
    main()
