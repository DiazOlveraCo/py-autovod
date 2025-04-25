from openai import OpenAI
import argparse
import json
import os
import sys
import time
from typing import List, Dict, Tuple, Optional
import re
from itertools import islice
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from tqdm import tqdm
import unittest

API_KEY = os.getenv("OPEN_ROUTER_KEY")

if not API_KEY:
    raise ValueError("Please set the OPEN_ROUTER_KEY environment variable")


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def load_clips(json_path: str) -> List[Dict]:
    """Load clips from JSON file with error handling."""
    try:
        with open(json_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Clips file not found: {json_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {json_path}")


def process_chunk(chunk_data: Tuple[List[Dict], int]) -> List[Dict]:
    """Process a single chunk of clips."""
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


def rank_clips_chunk(clips: List[Dict]) -> Optional[str]:
    """Rank a chunk of clips using the LLM API."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Local Test"
        },
    )

    prompt = f"""
    Analyze these clips for viral potential:

    {json.dumps(clips, indent=2)}

    For each clip, provide analysis in this exact format:
    
    1. **Clip Name: "[TITLE]"**
    Start: [START]s, End: [END]s
    Score: [1-10]
    Factors: [Key viral factors]
    Platforms: [Recommended platforms]

    Focus on measurable features in the data.
    """

    max_retries = 3
    retry_delay = 2
    model_name = "deepseek/deepseek-chat"

    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You analyze video clips for viral potential. Provide structured responses.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=1000,
            )

            if completion and completion.choices:
                return completion.choices[0].message.content

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(f"Failed to rank clips after {max_retries} attempts: {str(e)}")
                return None
    return None


def parse_clip_data(input_string: str) -> List[Dict]:
    """Robust parser for LLM output with multiple format support."""
    if not input_string:
        return []

    # Normalize line endings and remove empty lines
    lines = [line.strip() for line in input_string.split('\n') if line.strip()]
    normalized_input = '\n'.join(lines)
    
    # Split into individual clip sections
    clip_sections = re.split(r'\d+\.\s*\*\*Clip Name:', normalized_input)
    clips = []

    for section in clip_sections:
        if not section.strip():
            continue

        clip = {}
        
        # Extract name (handle different quote styles)
        name_match = re.search(r'"(.*?)"', section)
        if name_match:
            clip['name'] = name_match.group(1)
        
        # Extract start/end times (handle various formats)
        time_match = re.search(
            r'Start:\s*([\d.]+)\s*s?[,]?\s*End:\s*([\d.]+)\s*s?',
            section, re.IGNORECASE
        )
        if time_match:
            clip['start'] = float(time_match.group(1))
            clip['end'] = float(time_match.group(2))
        
        # Extract score (handle different formats)
        score_match = re.search(r'Score:\s*(\d+)(?:\s*/\s*10)?', section, re.IGNORECASE)
        if score_match:
            clip['score'] = int(score_match.group(1))
        
        # Extract factors (handle multi-line)
        factors_match = re.search(
            r'Factors:\s*(.+?)(?=\n\s*(?:Platforms|Score|$))', 
            section, re.DOTALL | re.IGNORECASE
        )
        if factors_match:
            clip['factors'] = factors_match.group(1).strip()
        
        # Extract platforms (handle different separators)
        platforms_match = re.search(
            r'Platforms:\s*(.+?)(?=\n\s*(?:Factors|Score|$))', 
            section, re.DOTALL | re.IGNORECASE
        )
        if platforms_match:
            platforms = re.sub(r'\s+', ' ', platforms_match.group(1).strip())
            clip['platforms'] = [p.strip() for p in re.split(r'[,/]', platforms) if p.strip()]

        if clip:  # Only add if we found any data
            clips.append(clip)

    return clips


def rank_all_clips_parallel(
    clips: List[Dict], 
    chunk_size: int = 5,
    num_processes: Optional[int] = None
) -> List[Dict]:
    """Rank clips in parallel with progress tracking."""
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)  # Limit to 8 processes

    chunks = chunk_list(clips, chunk_size)
    chunk_data = [(chunk, i) for i, chunk in enumerate(chunks)]

    all_ranked_clips = []
    pbar = tqdm(total=len(chunks), desc="Processing chunks")

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
    return sorted(all_ranked_clips, key=lambda x: x.get("score", 0), reverse=True)


def save_top_clips_json(
    clips: List[Dict], 
    output_file: str, 
    num_clips: int = 20
) -> None:
    """Save top clips to JSON file with metadata."""
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


class TestClipParser(unittest.TestCase):
    """Unit tests for the clip parser."""
    
    def test_parser(self):
        test_input = """
        1. **Clip Name: "Exciting Moment"**
        Start: 12.3s, End: 24.5s
        Score: 9
        Factors: High energy, crowd reaction
        Platforms: TikTok, YouTube Shorts

        2. **Clip Name: "Controversial Statement"**
        Platforms: Twitter, Instagram
        Factors: Political content, strong opinions
        Score: 8/10
        Start: 45s End: 52s
        """

        expected = [
            {
                'name': 'Exciting Moment',
                'start': 12.3,
                'end': 24.5,
                'score': 9,
                'factors': 'High energy, crowd reaction',
                'platforms': ['TikTok', 'YouTube Shorts']
            },
            {
                'name': 'Controversial Statement',
                'start': 45.0,
                'end': 52.0,
                'score': 8,
                'factors': 'Political content, strong opinions',
                'platforms': ['Twitter', 'Instagram']
            }
        ]

        result = parse_clip_data(test_input)
        self.assertEqual(len(result), 2)
        
        for i in range(2):
            for key in expected[i]:
                self.assertEqual(result[i][key], expected[i][key])

    def test_empty_input(self):
        self.assertEqual(parse_clip_data(""), [])

    def test_missing_fields(self):
        test_input = """
        1. **Clip Name: "Partial Clip"**
        Start: 10s, End: 20s
        Score: 5
        """
        result = parse_clip_data(test_input)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Partial Clip')
        self.assertNotIn('factors', result[0])


def main():
    parser = argparse.ArgumentParser(
        description="Rank and extract top viral video clips metadata."
    )
    parser.add_argument(
        "clips_json", 
        nargs='?',
        help="JSON file containing clip information"
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run unit tests instead of processing"
    )
    parser.add_argument(
        "--output_file",
        default="top_clips.json",
        help="Output JSON file for top clips"
    )
    parser.add_argument(
        "--num_clips", 
        type=int, 
        default=20,
        help="Number of top clips to extract"
    )
    parser.add_argument(
        "--chunk_size",
        type=int,
        default=5,
        help="Number of clips to process per API call"
    )
    parser.add_argument(
        "--num_processes",
        type=int,
        default=None,
        help="Number of parallel processes (default: CPU count)"
    )

    args = parser.parse_args()

    if args.test:
        unittest.main(argv=[''], exit=False)
        return

    if not args.clips_json:
        print("Error: No input file specified")
        parser.print_help()
        sys.exit(1)

    start_time = time.time()

    try:
        clips = load_clips(args.clips_json)
        ranked_clips = rank_all_clips_parallel(
            clips,
            args.chunk_size,
            args.num_processes,
        )

        save_top_clips_json(ranked_clips, args.output_file, args.num_clips)

        print(f"\nSuccessfully saved top {args.num_clips} clips to {args.output_file}")
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()