import sys
import time
import signal
from typing import Dict, List
from loguru import logger
from streamer_monitor import StreamerMonitor
import settings
import utils

class StreamManager:
    """Class to manage multiple streamer monitors."""

    def __init__(self):
        """Initialize the stream manager."""
        
        self.monitors: Dict[str, StreamerMonitor] = {}
        self.running = False
        self.retry_delay = 120

        if settings.config.has_option("general", "retry_delay"):
            self.retry_delay = settings.config.getint("general", "retry_delay")

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def get_streamers_list(self) -> List[str]:
        """Get the list of streamers to monitor from the configuration."""
        if not settings.config:
            return []

        if not settings.config.has_option("streamers", "streamers"):
            logger.error("No streamers defined in configuration")
            return []

        streamers_str = settings.config.get("streamers", "streamers")
        return set([s.strip() for s in streamers_str.strip(",").split(",") if s.strip()])

    def start(self):
        if self.running:
            logger.warning("Stream manager is already running")
            return

        streamers = self.get_streamers_list()
        if not streamers:
            logger.error("No streamers to monitor")
            return

        logger.info(
            f"Starting to monitor {len(streamers)} streamers: {', '.join(streamers)}"
        )

        # Create and start a monitor for each streamer
        for streamer_name in streamers:
            monitor = StreamerMonitor(streamer_name, self.retry_delay)
            self.monitors[streamer_name] = monitor
            monitor.daemon = True  # Set as daemon so they exit when main thread exits
            monitor.start()

        self.running = True
        logger.success("Stream manager started successfully")

    def stop(self):
        if not self.running:
            return

        logger.info("Stopping all streamer monitors..")

        # Stop all monitors
        for streamer_name, monitor in self.monitors.items():
            monitor.stop()
            monitor.join(timeout=0.02)

        self.monitors.clear()
        self.running = False

    def list_monitored_streamers(self) -> List[str]:
        return list(self.monitors.keys())

    def wait(self):
        prev_size = utils.get_size("recordings") 
        total = 0
        
        time.sleep(3)
        
        try:
            while self.running:
                cur_file_size = utils.get_size("recordings")  # in MB
                speed = cur_file_size - prev_size   
                prev_size = cur_file_size  
                total += speed

                print(f"\rDownload speed: {speed:.4f} MB/s | Total: {total:.4f} MB \n", end="", flush=True)
                
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            self.stop()