import sys
import time
import signal
from typing import Dict, List
from loguru import logger

from streamer_monitor import StreamerMonitor

class StreamManager:
    """Class to manage multiple streamer monitors."""
    
    def __init__(self, main_config):
        """Initialize the stream manager."""
        self.monitors: Dict[str, StreamerMonitor] = {}
        self.running = False
        self.config = main_config
        self.retry_delay = 60
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def get_streamers_list(self) -> List[str]:
        """Get the list of streamers to monitor from the configuration."""
        if not self.config:
            return []
        
        if not self.config.has_option("streamers", "streamers"):
            logger.error("No streamers defined in configuration")
            return []
        
        # Get the comma-separated list of streamers and strip whitespace
        streamers_str = self.config.get("streamers", "streamers")
        return [s.strip() for s in streamers_str.split(",") if s.strip()]
    
    def start(self):
        if self.running:
            logger.warning("Stream manager is already running")
            return
        
        streamers = self.get_streamers_list()
        if not streamers:
            logger.error("No streamers to monitor")
            return
        
        logger.info(f"Starting to monitor {len(streamers)} streamers: {', '.join(streamers)}")
        
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
        
        logger.info("Stopping all streamer monitors...")
        
        # Stop all monitors
        for streamer_name, monitor in self.monitors.items():
            logger.info(f"Stopping monitor for {streamer_name}")
            monitor.stop()
            monitor.join(timeout=1) 
        
        self.monitors.clear()
        self.running = False
        logger.info("All streamer monitors stopped")
    
    def add_streamer(self, streamer_name: str) -> bool:
        if streamer_name in self.monitors:
            logger.warning(f"Streamer {streamer_name} is already being monitored")
            return False
        
        monitor = StreamerMonitor(streamer_name, self.retry_delay)
        self.monitors[streamer_name] = monitor
        monitor.daemon = True
        monitor.start()
        
        logger.info(f"Started monitoring {streamer_name}")
        return True
    
    def remove_streamer(self, streamer_name: str) -> bool:
        if streamer_name not in self.monitors:
            logger.warning(f"Streamer {streamer_name} is not being monitored")
            return False
        
        monitor = self.monitors[streamer_name]
        monitor.stop()
        monitor.join(timeout=5)
        
        del self.monitors[streamer_name]
        logger.info(f"Stopped monitoring {streamer_name}")
        return True
    
    def list_monitored_streamers(self) -> List[str]:
        return list(self.monitors.keys())
    
    def wait_for_completion(self):
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            self.stop()
