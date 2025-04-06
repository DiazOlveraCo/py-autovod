import os
import sys
import argparse
from logger import logger
import settings

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Transcribe a .ts video file")
    parser.add_argument("file", help="Path to the .ts file to transcribe")
    parser.add_argument(
        "-m", "--model", help="Path to the Vosk model directory (overrides config)"
    )
    args = parser.parse_args()

    # Check if the file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        return 1

    # Check if the file is a .ts file
    if not args.file.lower().endswith(".ts"):
        logger.error(f"File is not a .ts file: {args.file}")
        return 1

    model_name = settings.config.get("transcription", "model_name")

    # Process the file
    logger.info(f"Transcribing file: {args.file}")
    logger.info(f"Using model: {model_name}")

    # success, transcript_path = process_ts_file(args.file, model_name, False)

    # if success:
    #     logger.success(f"Transcription saved to: {transcript_path}")
    #     return 0
    # else:
    #     logger.error("Transcription failed")
    #     return 1


if __name__ == "__main__":
    sys.exit(main())
