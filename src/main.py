#!/usr/bin/env python3

import os
import sys
import argparse
from loguru import logger

# Configure logger to include timestamp
logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> <level>{message}</level>",
    colorize=True,
)

from utils import is_docker, ensure_directories_exist
from stream_manager import StreamManager
from streamer_monitor import StreamerMonitor

VERSION = "1.1.0"

def main():
    logger.info(f"Starting AutoVOD v{VERSION}")
    
    parser = argparse.ArgumentParser(description="AutoVOD - Automatic VOD downloader for Twitch, Kick, and YouTube")
    parser.add_argument("-n", "--name", help="Single streamer name to monitor (legacy mode)")
    parser.add_argument("-a", "--add", help="Add a streamer to monitor")
    parser.add_argument("-r", "--remove", help="Remove a streamer from monitoring")
    parser.add_argument("-l", "--list", action="store_true", help="List currently monitored streamers")
    args = parser.parse_args()
    
    # Create recordings directory if it doesn't exist
    os.makedirs("recordings", exist_ok=True)
    
    # Single streamer mode (legacy)
    if args.name:
        logger.info(f"Running in legacy mode for single streamer: {args.name}")
        ensure_directories_exist(args.name)
        monitor = StreamerMonitor(args.name)
        monitor.run()
        return
    
    # Create the stream manager
    manager = StreamManager()
    
    # Handle command line arguments
    if args.add:
        if manager.add_streamer(args.add):
            logger.success(f"Added streamer: {args.add}")
        else:
            logger.error(f"Failed to add streamer: {args.add}")
        return
    
    if args.remove:
        if manager.remove_streamer(args.remove):
            logger.success(f"Removed streamer: {args.remove}")
        else:
            logger.error(f"Failed to remove streamer: {args.remove}")
        return
    
    if args.list:
        streamers = manager.list_monitored_streamers()
        if streamers:
            logger.info(f"Currently monitoring {len(streamers)} streamers: {', '.join(streamers)}")
        else:
            logger.info("No streamers are currently being monitored")
        return
    
    # Normal operation - start the manager and wait
    manager.start()
    manager.wait_for_completion()


if __name__ == "__main__":
    main()
