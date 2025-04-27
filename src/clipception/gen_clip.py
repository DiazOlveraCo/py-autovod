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
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPEN_ROUTER_KEY")

if not API_KEY:
    print("Error: OPEN_ROUTER_KEY environment variable is not set")
    raise ValueError("Please set it with: export OPEN_ROUTER_KEY='your_key_here'")

model_name = "deepseek/deepseek-chat" 

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
    
    prompt = f"""
    You are an expert content analyzer focusing on viral clip potential. 
    You can combine clips to form a longer clip, with the longest clip being 1 minute. Analyze these clips:

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

    For each clip, return ONLY valid JSON following this exact structure:
    {{\"clips\": [{{\"name\": \"[TITLE]\", \"start\": \"[START]\", \"end\": \"[END]\", \"score\": [1-10], \"factors\": \"[Key viral factors]\", \"platforms\": \"[Recommended platforms]\"}}]}}

    Rank clips by viral potential. Focus on measurable features in the data. No commentary. No markdown. Pure JSON only.
    """

    max_retries = 4
    retry_delay = 2

    # Get temperature and max_tokens from environment variables if available
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.5"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model = model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that ranks video clips. Keep explanations brief and focused on virality potential. Follow the format exactly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if completion and completion.choices:
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


def rank_all_clips_parallel(clips: List[Dict], chunk_size: int = 5, num_processes: int = None) -> List[Dict]:
    """Rank clips in parallel using multiple processes."""
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
    cleaned_str = input_string.replace("```json","").replace("```","").strip()
    try:
        # Parse the JSON string into a Python list of dictionaries
        clips = json.loads(cleaned_str)['clips']
        
        # Filter out invalid clip structures
        clips = [
            clip for clip in clips
            if all(key in clip for key in ('name', 'start', 'end', 'score', 'factors', 'platforms'))
        ]
        
        return clips
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing clip data: {e}")
        return []


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


def generate_clips(
    model_name1 : str,
    clips_json_path : str,
    output_file : str ,
    num_clips: int = 20,
    chunk_size: int = 10,
    num_processes=None,
):
    global model_name
    model_name = model_name1
    start_time = time.time()
    clips : List[Dict] = load_clips(clips_json_path)

    try:
        ranked_clips = rank_all_clips_parallel(
            clips,
            chunk_size,
            num_processes,
        )

        save_top_clips_json(ranked_clips, output_file, num_clips)

        print(f"\nSuccessfully saved top {num_clips} clips to {output_file}")
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error: {str(e)}")
