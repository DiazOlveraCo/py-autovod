# Script to turn video files into clips
import os
import sys
import argparse
from processor import processor


def main():
    parser = argparse.ArgumentParser(
        description="Process a video to generate clips based on transcription analysis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "video_path", nargs="?", help="Path to the input video file", default=None
    )

    args = parser.parse_args()

    video_path = ""
    if args.video_path:
        video_path = args.video_path
    else:
        print("Error: No video path provided")
        parser.print_help()
        sys.exit(1)

    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} not found")
        sys.exit(1)

    # Use the processor's existing method to process the video
    processor._process_single_file(video_path)


if __name__ == "__main__":
    main()
