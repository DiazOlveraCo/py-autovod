from moviepy import VideoFileClip
import json
import os


def extract_clip(input_file, output_dir, clip_data):
    """Extract a single clip based on the provided clip data"""
    try:
        # Create sanitized filename from clip name
        safe_name = "".join(
            c for c in clip_data["name"] if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        output_file = os.path.join(output_dir, f"{safe_name}.mp4")

        # Load the video file
        video = VideoFileClip(input_file)

        # Extract the clip using start and end times from JSON
        clip = video.subclipped(clip_data["start"], clip_data["end"])

        # Write the clip to a new file
        clip.write_videofile(output_file, codec="libx264")

        # Clean up
        clip.close()
        video.close()

        return True, output_file

    except Exception as e:
        return False, str(e)


def process_clips(input_file, output_dir, json_file, min_score=0):
    """Process all clips from the JSON file that meet the minimum score requirement"""

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Read and parse JSON data
    with open(json_file, "r") as f:
        data = json.load(f)
        print(data)

    # Process each clip that meets the score threshold
    successful_clips = []
    failed_clips = []

    for clip in data["top_clips"]:
        if clip["score"] >= min_score:
            success, result = extract_clip(input_file, output_dir, clip)
            if success:
                successful_clips.append((clip["name"], result))
            else:
                failed_clips.append((clip["name"], result))  # keyerror name

    # Print summary
    print(f"\nExtraction Summary:")
    print(f"Total clips processed: {len(successful_clips) + len(failed_clips)}")
    print(f"Successfully extracted: {len(successful_clips)}")
    print(f"Failed extractions: {len(failed_clips)}")

    if successful_clips:
        print("\nSuccessful clips:")
        for name, path in successful_clips:
            print(f"- {name}: {path}")

    if failed_clips:
        print("\nFailed clips:")
        for name, error in failed_clips:
            print(f"- {name}: {error}")