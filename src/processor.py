import queue
import threading
import time
import os
import sys
from pathlib import Path
from logger import logger
from settings import config
from dotenv import load_dotenv
from clipception.transcription import process_video
from clipception.gen_clip import generate_clips
from clipception.clip import process_clips


class Processor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Processor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.video_queue = queue.Queue()
            self.processing = False
            self.initialized = True

    def process(self, video_path):
        """Add a ts file to the queue to be processed with clipception."""

        if not os.path.exists(video_path):
            logger.debug(f"Can't queue video. Path {video_path} does not exist.")
            return

        logger.debug(f"Queuing video: {video_path}")

        self.video_queue.put(video_path)

        if not self.processing:
            threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        """Process in the queue one by one."""
        self.processing = True
        while not self.video_queue.empty():
            video_path = self.video_queue.get()
            logger.info(f"Processing video: {video_path}")

            self._process_single_file(video_path)

            logger.info(f"Finished processing: {video_path}")
            self.video_queue.task_done()
        self.processing = False

    def _process_single_file(self, video_path):
        """Process a video file with clipception to generate clips."""
        try:
            load_dotenv()

            if not os.getenv("OPEN_ROUTER_KEY"):
                logger.error("Error: OPEN_ROUTER_KEY environment variable is not set")
                logger.error(
                    "Please set it with: export OPEN_ROUTER_KEY='your_key_here'"
                )
                return

            num_clips = 10  # Default number of clips to generate
            min_score = 1  # Default minimum score threshold
            chunk_size = 10

            # Transcription settings
            model_size = config.get("transcription", "model_size")
            device = config.get("transcription", "device")

            # LLM settings
            model_name = config.get("llm", "model_name")
            temperature = config.getfloat("llm", "temperature", fallback=0.5)
            max_tokens = config.getint("llm", "max_tokens", fallback=1000)

            logger.info(f"Processing video: {video_path}")
            logger.info(f"Using transcription model: {model_size} on {device}")
            logger.info(
                f"Using LLM model: {model_name} (temp: {temperature}, max tokens: {max_tokens})"
            )

            # Ensure the video file exists
            if not os.path.exists(video_path):
                logger.error(f"Error: Video file {video_path} not found")
                return

            # Get file information
            filename_without_ext = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.dirname(video_path)

            # Step 1: Run enhanced transcription
            logger.info("Step 1: Generating enhanced transcription...")

            try:
                # Override device detection with config setting
                os.environ["FORCE_DEVICE"] = device
                process_video(video_path, model_size=model_size)
            except Exception as e:
                logger.error(f"Error during transcription: {str(e)}")
                return

            transcription_json = os.path.join(
                output_dir, f"{filename_without_ext}.enhanced_transcription.json"
            )
            if not os.path.exists(transcription_json):
                logger.error(
                    f"Error: Expected transcription file {transcription_json} was not generated"
                )
                return

            # Step 2: Generate clips JSON using GPU acceleration
            logger.info("Step 2: Processing transcription for clip selection...")

            output_file = os.path.join(output_dir, "top_clips_one.json")

            try:
                # Set environment variables for LLM parameters
                os.environ["LLM_TEMPERATURE"] = str(temperature)
                os.environ["LLM_MAX_TOKENS"] = str(max_tokens)

                generate_clips(
                    model_name,
                    transcription_json,
                    output_file,
                    num_clips=num_clips,
                    chunk_size=chunk_size,
                )
            except Exception as e:
                logger.error(f"Error during clip generation: {str(e)}")
                return

            if not os.path.exists(output_file):
                logger.error(f"Error: Top clips file {output_file} was not generated")
                return

            # Step 3: Extract video clips
            logger.info("Step 3: Extracting clips...")
            clips_output_dir = os.path.join(output_dir, "clips")

            try:
                process_clips(
                    video_path, clips_output_dir, output_file, min_score=min_score
                )
            except Exception as e:
                logger.error(f"Error during clip extraction: {str(e)}")
                return

            logger.success("All processing completed successfully! Generated files:")
            logger.info(f"1. Transcription: {transcription_json}")
            logger.info(f"2. Clip selections: {output_file}")
            logger.info(f"3. Video clips: {clips_output_dir}/")

        except Exception as e:
            logger.error(f"Error processing video {video_path}: {str(e)}")


processor = Processor()
