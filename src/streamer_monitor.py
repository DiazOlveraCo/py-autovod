import sys
import time
import threading
import subprocess
from typing import Optional
from logger import logger
from utils import (
    determine_source,
    check_stream_live,
    load_config,
)


class StreamerMonitor(threading.Thread):
    """Class to monitor and download streams for a single streamer."""

    def __init__(self, streamer_name: str, retry_delay: int = 60):
        super().__init__(name=f"m-{streamer_name}")
        self.streamer_name = streamer_name
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
                logger.error("Failed to load default config")
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

    def download_video(
        self, video_title: Optional[str] = None, video_description: Optional[str] = None
    ) -> bool:
        if not self.config:
            return False

        quality = self.config["streamlink"]["quality"]

        command = [
            "streamlink",
            "-o",
            f"recordings/{{author}}/{{id}}/{{author}}-{{time:%Y-%m-%d-%H-%M-%S}}.ts",
            self.stream_source_url,
            quality,
        ]

        if self.config.has_option("streamlink", "flags"):
            flags = self.config.get("streamlink", "flags").strip(",").split(",")
            flags = [flag.strip() for flag in flags if flag.strip()]
            command.extend(flags)

        try:
            self.current_process = subprocess.Popen(
                command, stdout=sys.stdout, stderr=subprocess.DEVNULL
            )
            retcode = self.current_process.wait()  # Wait until the stream ends
            success = retcode == 0
        except Exception as e:
            logger.error(f"Error running streamlink: {e}")
            success = False
        finally:
            self.current_process = None

        # If download was successful and transcription is enabled, process the video for transcription
        if success and self.config.getboolean(
            "transcription", "enabled", fallback=False
        ):
            self._process_transcription()

        return success

    def _process_transcription(self) -> None:
        """Process the latest downloaded file for transcription."""
        pass

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
                    logger.info(f"{self.streamer_name} is live")
                    video_title = None
                    video_description = None

                    # if self.config.getboolean("source", "api_calls", fallback=False):
                    #     video_title, video_description = fetch_metadata(
                    #         self.config["source"]["api_url"], self.streamer_name
                    #     )

                    download_success = self.download_video(
                        video_title, video_description
                    )

                    if download_success:
                        logger.success(
                            f"Stream for {self.streamer_name} downloaded successfully"
                        )
                else:
                    logger.info(
                        f"{self.streamer_name} is offline. Retrying in {self.retry_delay} seconds..."
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
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.debug("Process did not terminate in time; killing it")
                self.current_process.kill()
            self.current_process = None
        logger.debug(f"Stopped monitoring {self.streamer_name}")
