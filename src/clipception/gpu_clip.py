from openai import OpenAI
import argparse
import json
import os
import sys
import time
from typing import List, Dict, Tuple
import re
from itertools import islice
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from tqdm import tqdm


API_KEY = os.getenv("OPEN_ROUTER_KEY")

if not API_KEY:
    raise ValueError("Please set the OPEN_ROUTER_KEY environment variable")


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def load_clips(json_path: str) -> List[Dict]:
    try:
        with open(json_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Clips file not found: {json_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {json_path}")


def process_chunk(chunk_data: Tuple[List[Dict], int]) -> List[Dict]:
    """Process a single chunk of clips using GPU acceleration."""
    clips, chunk_id = chunk_data

    try:
        ranked_results = rank_clips_chunk(clips)
        if ranked_results:
            parsed_chunk = parse_clip_data(ranked_results)
            return parsed_chunk
        return []
    except Exception as e:
        print(f"Warning: Failed to process chunk {chunk_id}: {str(e)}")
        return []


def rank_clips_chunk(clips: List[Dict]) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
        default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Local Test"},
    )

    print("CLIPS:")
    for i, dictionary in enumerate(clips):
        print(f"dict {i+1}:")
        print(i, dictionary)

    prompt = f"""
    You are an expert content analyzer focusing on viral clip potential. 
    Analyze these clips:

    {json.dumps(clips, indent=2)}

    For each clip, evaluate using:

    1. Audio Engagement (40% weight):
    - Volume patterns and variations
    - Voice intensity and emotional charge 
    - Acoustic characteristics

    2. Content Analysis (60% weight):
    - Topic relevance and timeliness
    - Controversial or debate-sparking elements
    - "Quotable" phrases
    - Discussion potential

    For each clip, provide in this exact format:
    1. **Clip Name: "[TITLE]"**
    Start: [START]s, End: [END]s
    Score: [1-10]
    Factors: [Key viral factors]
    Platforms: [Recommended platforms]

    Rank clips by viral potential. Focus on measurable features in the data.
    """

    max_retries = 4
    retry_delay = 2
    model_name = "deepseek/deepseek-chat"  # "gpt-4-turbo-preview"

    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that ranks video clips. Keep explanations brief and focused on virality potential.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=1000,
            )

            if completion and completion.choices:
                print(completion.choices[0].message.content)
                return completion.choices[0].message.content

        except Exception as e:
            if attempt < max_retries - 1:
                print(
                    f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds..."
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise Exception(
                    f"Failed to rank clips after {max_retries} attempts: {str(e)}"
                )
    return None


def rank_all_clips_parallel(
    clips: List[Dict], chunk_size: int = 5, num_processes: int = None
) -> List[Dict]:
    """Rank clips in parallel using multiple processes and GPU acceleration."""
    if num_processes is None:
        num_processes = mp.cpu_count()

    chunks = chunk_list(clips, chunk_size)
    chunk_data = [(chunk, i) for i, chunk in enumerate(chunks)]

    all_ranked_clips = []

    # Setup progress bar
    pbar = tqdm(total=len(chunks), desc="Processing chunks")

    # Use ThreadPoolExecutor for parallel API calls
    with ThreadPoolExecutor(max_workers=num_processes) as executor:
        futures = [executor.submit(process_chunk, data) for data in chunk_data]

        for future in futures:
            try:
                result = future.result()
                all_ranked_clips.extend(result)
                pbar.update(1)
            except Exception as e:
                print(f"Warning: Chunk processing failed: {str(e)}")

    pbar.close()

    # Final sorting of all clips
    return sorted(all_ranked_clips, key=lambda x: x.get("score", 0), reverse=True)


def parse_clip_data(input_string: str) -> list[dict]:
    if not input_string:
        return []

    clips = []
    current_clip = {}
    lines: list[str] = input_string.split("\n")

    for i in range(len(lines)):
        line = lines[i].strip()
        if not line:
            continue

        if re.match(r"^\d+\.\s\*\*Clip Name:", line):
            if current_clip:
                clips.append(current_clip)
                current_clip = {}

            name_match = re.search(r'Clip Name: "(.*?)"', line)
            if name_match:
                current_clip["name"] = name_match.group(1)

        elif "Start:" in line and "End:" in line:
            time_match = re.search(r"Start: ([\d.]+)s, End: ([\d.]+)s", line)
            if time_match:
                current_clip["start"] = float(time_match.group(1))
                current_clip["end"] = float(time_match.group(2))

        elif "Score:" in line:
            score_match = re.search(r"Score: (\d+)", line)
            if score_match:
                current_clip["score"] = int(score_match.group(1))

        elif "Factors:" in line:
            factors_match = re.search(r"Factors: (.+)", line)
            if factors_match:
                current_clip["factors"] = factors_match.group(1)

        elif "Platforms:" in line:
            platforms_match = re.search(r"Platforms: (.+)", line)
            if platforms_match:
                current_clip["platforms"] = platforms_match.group(1)

    if current_clip:
        clips.append(current_clip)

    print("len of clips: " + str(len(clips)))
    time.sleep(1)
    return clips


def save_top_clips_json(
    clips: List[Dict], output_file: str, num_clips: int = 20
) -> None:
    top_clips = clips[:num_clips]
    output_data = {
        "top_clips": top_clips,
        "total_clips": len(clips),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)
    except Exception as e:
        raise RuntimeError(f"Failed to save JSON file: {str(e)}")


def transcribe_clips(
    clips_json,
    output_file,
    num_clips: int = 20,
    chunk_size: int = 5,
    num_processes=None,
):
    start_time = time.time()

    try:
        clips = clips_json
        ranked_clips = rank_all_clips_parallel(clips, chunk_size, num_processes)

        save_top_clips_json(ranked_clips, output_file, num_clips)

        print(f"\nSuccessfully saved top {num_clips} clips to {output_file}")
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Rank and extract top viral video clips metadata using GPU acceleration."
    )
    parser.add_argument("clips_json", help="JSON file containing clip information")
    parser.add_argument(
        "--output_file",
        default="top_clips_one.json",
        help="Output JSON file for top clips",
    )
    parser.add_argument(
        "--num_clips", type=int, default=20, help="Number of top clips to extract"
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=5,
        help="Number of clips to process per API call",
    )
    parser.add_argument(
        "--num_processes",
        type=int,
        default=None,
        help="Number of parallel processes (default: CPU count)",
    )

    args = parser.parse_args()
    start_time = time.time()

    try:
        clips = load_clips(args.clips_json)
        ranked_clips = rank_all_clips_parallel(
            clips, args.chunk_size, args.num_processes
        )

        save_top_clips_json(ranked_clips, args.output_file, args.num_clips)

        print(f"\nSuccessfully saved top {args.num_clips} clips to {args.output_file}")
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
