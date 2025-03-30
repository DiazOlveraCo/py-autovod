import sys
import time
import threading
from datetime import datetime
from loguru import logger

from utils import (
    run_command,
    determine_source,
    check_stream_live,
    fetch_metadata,
    load_config,
)

class StreamerMonitor(threading.Thread):
    """Class to monitor and download streams for a single streamer."""
    
    def __init__(self, streamer_name: str, retry_delay: int = 60):
        """Initialize the streamer monitor.
        
        Args:
            streamer_name: The name of the streamer to monitor
            retry_delay: Time in seconds to wait between checks if stream is offline
        """
        super().__init__(name=f"Monitor-{streamer_name}")
        self.streamer_name = streamer_name
        self.retry_delay = retry_delay
        self.running = False
        self.config = None
        self.stream_source_url = None
        
        # Initialize
        self._load_configuration()
    
    def _load_configuration(self) -> bool:
        """Load the streamer-specific configuration."""
        self.config = load_config(self.streamer_name)
        if not self.config:
            logger.error(f"Failed to load configuration for {self.streamer_name}")
            return False
        
        stream_source = self.config["source"]["stream_source"]
        self.stream_source_url = determine_source(stream_source, self.streamer_name)
        
        if not self.stream_source_url:
            logger.error(f"Unknown stream source: {stream_source} for {self.streamer_name}")
            return False
        
        return True
    
    def process_video(self, video_title=None, video_description=None) -> bool:
        """Process and download a live stream."""
        if not self.config:
            return False
        
        quality = self.config["streamlink"]["quality"]
        date_str = datetime.now().strftime("%d-%m-%Y")
        
        # Build command with flags from config
        command = [
            "streamlink",
            "-o",
            f"recordings/{self.streamer_name}/{{author}}-{{id}}-{{time:%Y%m%d%H%M%S}}.ts",
            self.stream_source_url,
            quality,
        ]
        
        # Add flags from config if available
        if self.config.has_option("streamlink", "flags"):
            flags = self.config.get("streamlink", "flags").split(",")
            # Strip whitespace from each flag
            flags = [flag.strip() for flag in flags if flag.strip()]
            command.extend(flags)
        
        result = run_command(
            command,
            stdout=sys.stdout,
        )
        
        # streamlink returns when stream ends
        return result.returncode == 0
    
    def run(self):
        """Main monitoring loop."""
        if not self.config or not self.stream_source_url:
            logger.error(f"Cannot start monitoring for {self.streamer_name}: missing configuration")
            return
        
        self.running = True
        logger.info(f"Started monitoring {self.streamer_name}")
        
        while self.running:
            try:
                if check_stream_live(self.stream_source_url):
                    logger.info(f"{self.streamer_name} is live")
                    
                    video_title = None
                    video_description = None
                    
                    if self.config.getboolean("source", "api_calls", fallback=False):
                        video_title, video_description = fetch_metadata(
                            self.config["source"]["api_url"], self.streamer_name
                        )
                    
                    download_success = self.process_video(video_title, video_description)
                    
                    if download_success:
                        logger.success(f"Stream for {self.streamer_name} downloaded successfully")
                    else:
                        logger.error(f"Stream download failed for {self.streamer_name}")
                
                else:
                    logger.info(f"{self.streamer_name} is offline. Retrying in {self.retry_delay} seconds...")
            
            except Exception as e:
                logger.error(f"Error monitoring {self.streamer_name}: {e}")
            
            # Sleep before next check
            time.sleep(self.retry_delay)
    
    def stop(self):
        """Stop the monitoring thread."""
        self.running = False
        logger.info(f"Stopped monitoring {self.streamer_name}")
