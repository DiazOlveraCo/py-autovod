#!/usr/bin/env python3

import os
import sys
import argparse
from loguru import logger
from utils import (is_docker, load_main_config)
import settings
from stream_manager import StreamManager
from streamer_monitor import StreamerMonitor

# Configure logger to include timestamp
logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> <level>{message}</level>",
    colorize=True,
)

settings.init()

def main():
    version = settings.config.get("general", "version")

    logger.info(f"Starting AutoVOD v{version}")
    
    parser = argparse.ArgumentParser(description="AutoVOD - Automatic VOD downloader for Twitch, Kick, and YouTube")
    parser.add_argument("-n", "--name", help="Single streamer name to monitor")
    parser.add_argument("-a", "--add", help="Add a streamer to monitor")
    parser.add_argument("-r", "--remove", help="Remove a streamer from monitoring")
    parser.add_argument("-l", "--list", action="store_true", help="List currently monitored streamers")
    parser.add_argument("-v", "--version", action="store_true", help="Display the current version of AutoVOD")
    args = parser.parse_args()
    
    # Create recordings directory if it doesn't exist
    os.makedirs("recordings", exist_ok=True)
    
    # Display version and exit
    if args.version:
        print(f"AutoVOD v{version}")
        return
        
    # Single streamer mode
    if args.name:
        logger.info(f"Running for a single streamer: {args.name}")
        monitor = StreamerMonitor(args.name, settings.config.get("general","retry_delay"))
        monitor.run()
        return
    
    # Create the stream manager
    manager = StreamManager(settings.config)
    
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
