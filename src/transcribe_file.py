import os
import sys
import argparse
import logger
from settings import config


def validate_file(file_path: str) -> bool:
    # Check if the file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    # Check if the file is a .ts file
    if not file_path.lower().endswith(".ts"):
        logger.error(f"File is not a .ts file: {file_path}")
        return False

    return True


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Transcribe a .ts video file")
    parser.add_argument("file", help="Path to the .ts file to transcribe")
    parser.add_argument(
        "-m", "--model", help="Path to the Vosk model directory (overrides config)"
    )
    args = parser.parse_args()

    if not validate_file(args.file):
        return 1

    # Get model name from config or command line
    model_name = args.model or config.get("transcription", "model_name")

    # Process the file
    logger.info(f"Transcribing file: {args.file}")
    logger.info(f"Using model: {model_name}")

    # Commented out as in the original code
    # success, transcript_path = process_ts_file(args.file, model_name, False)
    #
    # if success:
    #     logger.success(f"Transcription saved to: {transcript_path}")
    #     return 0
    # else:
    #     logger.error("Transcription failed")
    #     return 1

    # Placeholder return until the commented code is implemented
    return 0


if __name__ == "__main__":
    sys.exit(main())
