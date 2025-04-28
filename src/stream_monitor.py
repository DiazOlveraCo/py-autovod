import sys
import os
import time
import threading
import subprocess
import datetime
from typing import Optional
from logger import logger
from utils import determine_source, check_stream_live, load_config
from processor import processor


class StreamMonitor(threading.Thread):
    """Class to monitor and download streams for a single streamer."""

    def __init__(self, streamer_name: str, retry_delay: int = 60):
        super().__init__(name=f"m-{streamer_name}")
        self.streamer_name = streamer_name.lower()
        self.retry_delay = retry_delay
        self.running = False
        self.config = None
        self.stream_source_url = None
        self.current_process = None  # Store the running streamlink subprocess
        self._load_configuration()

    def _load_configuration(self) -> bool:
        self.config = load_config(self.streamer_name)
        if not self.config:
            self.config = load_config("default")
            if not self.config:
                logger.error("Failed to load default config file.")
                return False

        # Get stream source from config
        try:
            stream_source = self.config["source"]["stream_source"]
            self.stream_source_url = determine_source(stream_source, self.streamer_name)
        except KeyError:
            logger.error(f"Missing source configuration for {self.streamer_name}")
            return False

        if not self.stream_source_url:
            logger.error(
                f"Unknown stream source: {stream_source} for {self.streamer_name}"
            )
            return False

        return True

    def _find_latest_video_file(self) -> str:
        """Find the most recently modified .ts file in the streamer's recordings directory."""
        base_dir = f"recordings/{self.streamer_name}"

        if not os.path.exists(base_dir):
            logger.error(f"Recordings directory not found: {base_dir}")
            return ""

        stream_dirs = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                stream_dirs.append(item_path)

        if not stream_dirs:
            logger.error(f"No stream directories found in {base_dir}")
            return ""

        # Find the most recently modified .ts file across all stream directories
        latest_file = ""
        latest_time = 0

        for stream_dir in stream_dirs:
            for file in os.listdir(stream_dir):
                file_path = os.path.join(stream_dir, file)
                mod_time = os.path.getmtime(file_path)

                if mod_time > latest_time:
                    latest_time = mod_time
                    latest_file = file_path

        if latest_file:
            logger.debug(f"Found latest video file: {latest_file}")
            return latest_file
        else:
            logger.error(f"No .ts files found in {base_dir} subdirectories")
            return ""

    def download_video(self) -> tuple[bool, str]:
        if not self.config:
            return False, ""

        quality = self.config["streamlink"]["quality"]
        current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        output_path = f"recordings/{self.streamer_name}/{{id}}/{self.streamer_name}-{current_time}.ts"

        # Ensure the base directory exists
        base_dir = f"recordings/{self.streamer_name}"
        os.makedirs(base_dir, exist_ok=True)

        command = ["streamlink", "-o", output_path, self.stream_source_url, quality]

        if self.config.has_option("streamlink", "flags"):
            flags = self.config.get("streamlink", "flags").strip(",").split(",")
            flags = [flag.strip() for flag in flags if flag.strip()]
            command.extend(flags)

        try:

            # Start the download process
            self.current_process = subprocess.Popen(
                command, stdout=sys.stdout, stderr=subprocess.DEVNULL
            )
            retcode = self.current_process.wait()  # Wait until the stream ends
            success = retcode == 0

            if success:
                actual_path = self._find_latest_video_file()

                if actual_path and os.path.exists(actual_path):
                    logger.debug(f"Found downloaded file: {actual_path}")
                    return True, actual_path
                else:
                    logger.debug(
                        f"Found file {actual_path} but it appears to be from a previous download"
                    )

                logger.warning("Could not find the downloaded file")
                return True, ""
            else:
                return False, ""

        except Exception as e:
            logger.error(f"Error running streamlink: {e}")
            return False, ""
        finally:
            self.current_process = None

    def run(self) -> None:
        if not self.config or not self.stream_source_url:
            logger.error(
                f"Cannot start monitoring for {self.streamer_name}: missing configuration"
            )
            return

        self.running = True
        logger.info(f"Started monitoring {self.streamer_name}")

        while self.running:
            try:
                if check_stream_live(self.stream_source_url):
                    logger.success(f"{self.streamer_name} is live!")

                    download_success, video_path = self.download_video()

                    if download_success:
                        logger.success(
                            f"Stream for {self.streamer_name} downloaded successfully"
                        )
                        if video_path:
                            # Process video with streamer name
                            processor.process(video_path, self.streamer_name,self.config)
                        else:
                            logger.error(
                                "Downloaded file path not found, cannot process video"
                            )
                    else:
                        logger.warning(
                            f"Failed to download stream for {self.streamer_name}"
                        )

                else:
                    logger.info(
                        f"{self.streamer_name} is offline. Retrying in {self.retry_delay} seconds.."
                    )
            except Exception as e:
                logger.error(f"Error monitoring {self.streamer_name}: {e}")

            time.sleep(self.retry_delay)

    def stop(self) -> None:
        self.running = False
        if self.current_process is not None:
            logger.debug(f"Terminating streamlink process for {self.streamer_name}")
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.debug("Process did not terminate in time; killing it")
                self.current_process.kill()
            self.current_process = None
        logger.debug(f"Stopped monitoring {self.streamer_name}")
