#!/usr/bin/env python3

import os
import sys
import argparse
from loguru import logger
import settings # note that settings are only loaded upon import
from stream_manager import StreamManager
from streamer_monitor import StreamerMonitor

logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> | <level>{message}</level>",
    colorize=True,
)

def main():
    version = settings.config.get("general", "version")

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
