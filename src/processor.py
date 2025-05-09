import queue
import threading
import os
from logger import logger
from settings import config
from utils import run_command

# clipception
from transcription import process_video,MIN_DURATION
from gen_clip import generate_clips
from clip import process_clips


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

    def process(self, video_path, streamer_name, streamer_config):
        """Add a ts file to the queue to be processed with clipception."""

        if not os.path.exists(video_path):
            logger.warning(f"Can't queue video. Path {video_path} does not exist.")
            return

        logger.debug(f"Queuing video: {video_path}")

        # Add both video path and streamer name to the queue
        self.video_queue.put((video_path, streamer_name, streamer_config))

        if not self.processing:
            threading.Thread(target=self._process_queue, daemon=True).start()

    def _process_queue(self):
        """Process in the queue one by one."""
        self.processing = True
        while not self.video_queue.empty():
            video_path, streamer_name, streamer_config = self.video_queue.get()
            new_video_path = video_path
            logger.info(f"Processing video: {video_path}")

            # Convert and re-encode if configured
            try:
                # Convert .ts to a new format
                if streamer_config.getboolean("local", "save_locally"):
                    new_video_path = self._convert(video_path)

                if streamer_config.getboolean("encoding", "re_encode"):
                    new_video_path = self._encode(new_video_path, streamer_config)

                if new_video_path:
                    logger.debug(f"Video saved locally: {new_video_path}")
            except Exception as e:
                logger.error(f"Error encoding/saving video locally: {str(e)}")

            # Process with clipception
            if config.getboolean(
                "clipception", "enabled"
            ) and streamer_config.getboolean("clipception", "enabled"):
                self._process_single_file(new_video_path, streamer_name)

            logger.info(f"Finished processing: {new_video_path}")
            self.video_queue.task_done()
        self.processing = False

    def _convert(self, input_path: str) -> str:
        """Converts a file to a new format using ffmpeg."""

        output_path = os.path.splitext(input_path)[0] + ".mp4"

        command = ['ffmpeg', '-i', input_path, '-c', 'copy', output_path,"-loglevel","error"]
        run_command(command)

        if MIN_DURATION < 130:
            command = ['ffmpeg', '-i', output_path,
                '-vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"''-c', 
                'copy', "s"+output_path,"-loglevel","error"]
            run_command(command)

        return output_path

    def _encode(self, video_path, streamer_config):
        try:
            output_path = ""
            codec = streamer_config.get("encoding", "codec", fallback="libx265")
            crf = streamer_config.get("encoding", "crf", fallback="25")
            preset = streamer_config.get("encoding", "preset", fallback="medium")
            log_level = streamer_config.get("encoding", "log", fallback="error")

            # Build FFmpeg command
            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-c:v",
                codec,
                "-crf",
                crf,
                "-preset",
                preset,
                "-c:a",
                "copy",  # Copy audio stream
                "-loglevel",
                log_level,
                output_path,
            ]

            # Execute FFmpeg command
            logger.info(f"Re-encoding video with FFmpeg: {' '.join(ffmpeg_cmd)}")
            result = run_command(ffmpeg_cmd)

            if result.returncode != 0:
                logger.error(f"FFmpeg encoding failed: {result.stderr}")
                return None

            logger.success(f"Video saved locally: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error encoding/saving video locally: {str(e)}")
            return None

    def _process_single_file(self, video_path, streamer_name=None):
        """Process a video file with clipception to generate clips."""
        try:
            num_clips = config.getint(
                "clipception", "num_clips", fallback=10
            )  # Default number of clips to generate
            min_score = 0  # Default minimum score threshold
            chunk_size = 10

            logger.info(f"Processing video: {video_path}")

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
                process_video(video_path)
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
                generate_clips(
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
