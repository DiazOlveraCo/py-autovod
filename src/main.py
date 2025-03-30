#!/usr/bin/env python3

import os
import sys
import argparse
from loguru import logger
from utils import (is_docker, load_config)
import settings
from stream_manager import StreamManager
from streamer_monitor import StreamerMonitor

logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> | <level>{message}</level>",
    colorize=True,
)

settings.init()


def main():
    version = settings.config.get("general", "version")

    print(f"Starting AutoVOD v{version}")
    
    parser = argparse.ArgumentParser(description="AutoVOD - Automatic VOD downloader for Twitch, Kick, and YouTube")

    parser.add_argument("-n", "--name", help="Single streamer name to monitor")
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Display the current version of AutoVOD",
    )
    args = parser.parse_args()
    
    if not os.path.exists("recordings"):
        try:
            os.mkdir("recordings")
        except:
            pass

    # Display version and exit
    if args.version:
        print(f"AutoVOD v{version}")
        return

    # Create the stream manager
    manager = StreamManager()
    
    # start the manager and wait
    manager.start()
    manager.wait_for_completion()


if __name__ == "__main__":
    main()