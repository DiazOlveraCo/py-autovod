import subprocess
import os
import sys
import uuid
from pathlib import Path
import tempfile
import time
import glob
import re
import shutil
from clipception.transcription import process_video
from clipception.gpu_clip import transcribe_clips
from clipception.clip import process_clips


def run_script(command):
    try:
        print(f"Running: {command}")
        process = subprocess.run(command, check=True, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {str(e)}")
        return False


def main():
    # Check for OpenRouter API key
    if not os.getenv("OPEN_ROUTER_KEY"):
        print("Error: OPEN_ROUTER_KEY environment variable is not set")
        print("Please set it with: export OPEN_ROUTER_KEY='your_key_here'")
        sys.exit(1)

    video_path = sys.argv[1]
    filename_without_ext = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.dirname(video_path)

    # Step 1: Run enhanced transcription
    print("\nStep 1: Generating enhanced transcription...")

    process_video(video_path, model_size="tiny")

    transcription_json = os.path.join(
        output_dir, f"{filename_without_ext}.enhanced_transcription.json"
    )
    if not os.path.exists(transcription_json):
        print(
            f"Error: Expected transcription file {transcription_json} was not generated"
        )
        sys.exit(1)

    # Step 2: Generate clips JSON using GPU acceleration
    print("\nStep 2: Processing transcription for clip selection...")

    output_file = os.path.join(output_dir, "top_clips_one.json")
    transcribe_clips(transcription_json, output_file, num_clips=20, chunk_size=5)

    if not os.path.exists(output_file):
        print(f"Error: Top clips file {output_file} was not generated")
        sys.exit(1)

    # Step 3: Extract video clips
    print("\nStep 3: Extracting clips...")
    clips_output_dir = os.path.join(output_dir, "clips")
    os.makedirs(clips_output_dir, exist_ok=True)

    process_clips(video_path, clips_output_dir, output_dir, min_score=0)

    print("\nAll processing completed successfully!")
    print(f"Generated files:")
    print(f"1. Transcription: {transcription_json}")
    print(f"2. Clip selections: {output_file}")
    print(f"3. Video clips: {clips_output_dir}/")


if __name__ == "__main__":
    main()
