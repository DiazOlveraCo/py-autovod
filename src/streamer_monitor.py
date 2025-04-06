import sys
import time
import threading
import os
from typing import Optional
from logger import logger
from settings import config
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
        super().__init__(name=f"m-{streamer_name}")
        self.streamer_name = streamer_name
        self.retry_delay = retry_delay
        self.running = False
        self.config = None
        self.stream_source_url = None

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

        result = run_command(
            command,
            stdout=sys.stdout,
        )

        # streamlink returns when stream ends
        success = result.returncode == 0

        # If download was successful and transcription is enabled, process the video for transcription
        if success and config.getboolean("transcription", "enabled", fallback=False):
            self._process_transcription()

        return success

    def _process_transcription(self) -> None:
        """Process the latest downloaded file for transcription."""
        # Find the most recently downloaded file
        streamer_dir = f"recordings/{self.streamer_name}"
        if not os.path.exists(streamer_dir):
            logger.warning(f"Directory not found: {streamer_dir}")
            return

        files = [
            os.path.join(streamer_dir, f)
            for f in os.listdir(streamer_dir)
            if f.endswith(".ts")
        ]

        if not files:
            logger.warning(f"No .ts files found in {streamer_dir}")
            return

        # Sort by modification time, newest first
        latest_file = max(files, key=os.path.getmtime)
        logger.info(f"Found latest recording: {latest_file}")

        # Convert to MP4
        mp4_file = latest_file.replace(".ts", ".mp4")
        convert_result = run_command(
            [
                "ffmpeg",
                "-i",
                latest_file,
                "-c",
                "copy",
                mp4_file,
            ],
            stdout=sys.stdout,
        )

        if convert_result.returncode != 0:
            logger.error(f"Failed to convert {latest_file} to MP4")
            return

        # model_name = config.get("transcription", "model_name")
        # cleanup_wav = config.getboolean(
        #     "transcription", "cleanup_wav", fallback=True
        # )

        # Process the file for transcription (commented out as in original)
        # try:
        #     transcription_success, transcript_path = process_ts_file(
        #         latest_file, model_name, cleanup_wav
        #     )
        #
        #     if transcription_success:
        #         logger.success(f"Transcription saved to {transcript_path}")
        #     else:
        #         logger.error("Transcription failed")
        # except Exception as e:
        #     logger.error(f"Error during transcription: {e}")

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
        logger.info(f"Stopped monitoring {self.streamer_name}")
