import os
import sys
from pathlib import Path
import argparse
from settings import config
from dotenv import load_dotenv

load_dotenv()

def main():
    num_clips = 10
    min_score = 0

    # my system can only handle 2 video processes at a time.

    # parser = argparse.ArgumentParser(
    #     description='Process a video to generate clips based on transcription analysis.',
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter
    # )

    # parser.add_argument(
    #     'video_path',
    #     help='Path to the input video file'
    # )

    # args = parser.parse_args()

    # Check for OpenRouter API key
    if not os.getenv("OPEN_ROUTER_KEY"):
        print("Error: OPEN_ROUTER_KEY environment variable is not set")
        print("Please set it with: export OPEN_ROUTER_KEY='your_key_here'")
        sys.exit(1)

    video_path = "recordings/Meisaka/319736676348/Meisaka-2025-04-17-21-48-20.ts" #args.video_path
    filename_without_ext = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.dirname(video_path)

    # Step 1: Run enhanced transcription
    #print("\nStep 1: Generating enhanced transcription..")

    from clipception.transcription import process_video

    print("Imported script.")

    model_size = config.get("transcription", "model_size")
    print(model_size)

    process_video(video_path, model_size=model_size)

    transcription_json = os.path.join(
        output_dir, f"{filename_without_ext}.enhanced_transcription.json"
    )
    if not os.path.exists(transcription_json):
        print(f"Error: Expected transcription file {transcription_json} was not generated")
        sys.exit(1)

    # Step 2: Generate clips JSON using GPU acceleration
    print("\nStep 2: Processing transcription for clip selection..")

    output_file = os.path.join(output_dir, "top_clips_one.json")
    # TODO write a function to calculate num_clips

    from clipception.gpu_clip import transcribe_clips

    transcribe_clips(transcription_json, output_file, num_clips = num_clips, chunk_size=5)

    if not os.path.exists(output_file):
        print(f"Error: Top clips file {output_file} was not generated")
        sys.exit(1)

    # Step 3: Extract video clips
    print("\nStep 3: Extracting clips..")
    clips_output_dir = os.path.join(output_dir, "clips")

    from clipception.clip import process_clips

    process_clips(video_path, clips_output_dir, output_file, min_score = min_score)

    print("\nAll processing completed successfully! Generated files:")
    print(f"1. Transcription: {transcription_json}")
    print(f"2. Clip selections: {output_file}")
    print(f"3. Video clips: {clips_output_dir}/")


if __name__ == "__main__":
    main()
