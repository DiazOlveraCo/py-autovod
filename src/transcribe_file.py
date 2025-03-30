#!/usr/bin/env python3

import os
import sys
import argparse
from loguru import logger
import settings
from transcription import process_ts_file, check_dependencies

# Configure logger to include timestamp
logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> <level>{message}</level>",
    colorize=True,
)

def main():
    # Initialize settings
    settings.init()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Transcribe a .ts video file")
    parser.add_argument("file", help="Path to the .ts file to transcribe")
    parser.add_argument("-m", "--model", help="Path to the Vosk model directory (overrides config)")
    parser.add_argument("--keep-wav", action="store_true", help="Keep the intermediate WAV file")
    args = parser.parse_args()
    
    # Check if the file exists
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        return 1
    
    # Check if the file is a .ts file
    if not args.file.lower().endswith(".ts"):
        logger.error(f"File is not a .ts file: {args.file}")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Required dependencies not available")
        logger.error("Please install ffmpeg and vosk: pip install vosk")
        return 1
    
    # Get model path from arguments or config
    model_path = args.model
    if not model_path:
        model_path = settings.config.get("transcription", "model_path")
    
    # Check if model path exists
    if not os.path.exists(model_path):
        logger.error(f"Model path not found: {model_path}")
        logger.error("Download a model from https://alphacephei.com/vosk/models")
        logger.error("And update the model_path in config.ini or provide it with --model")
        return 1
    
    # Process the file
    logger.info(f"Transcribing file: {args.file}")
    logger.info(f"Using model: {model_path}")
    
    success, transcript_path = process_ts_file(
        args.file,
        model_path,
        not args.keep_wav  # Cleanup WAV if not keep_wav
    )
    
    if success:
        logger.success(f"Transcription saved to: {transcript_path}")
        return 0
    else:
        logger.error("Transcription failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
