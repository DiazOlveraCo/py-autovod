#!/usr/bin/env python3

"""
Example script demonstrating how to use the transcription module directly.
This can be used as a reference for integrating transcription into other Python scripts.
"""

import os
import sys
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transcription import (
    check_dependencies,
    extract_audio_from_ts,
    transcribe_audio,
    save_transcript,
    process_ts_file
)

def example_full_process():
    """Example of processing a .ts file using the high-level function."""
    
    # Check if dependencies are available
    if not check_dependencies():
        print("Required dependencies not available")
        print("Please install ffmpeg and vosk: pip install vosk")
        return
    
    # Path to the .ts file
    ts_file = "recordings/deslic/deslic-320111820413-20250330001707.ts"
    
    # Path to the Vosk model
    model_path = "models/vosk-model-small-en-us-0.15"
    
    # Process the file
    print(f"Processing file: {ts_file}")
    success, transcript_path = process_ts_file(ts_file, model_path, cleanup_wav=True)
    
    if success:
        print(f"Transcription saved to: {transcript_path}")
        
        # Load and print a sample of the transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = json.load(f)
            
        print("\nTranscript sample:")
        print(f"Full text: {transcript['text'][:100]}...")
        print("\nSegments:")
        for i, segment in enumerate(transcript['segments'][:3]):
            print(f"  {i+1}. [{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")
        
        if len(transcript['segments']) > 3:
            print(f"  ... and {len(transcript['segments']) - 3} more segments")
    else:
        print("Transcription failed")

def example_step_by_step():
    """Example of processing a .ts file step by step."""
    
    # Check if dependencies are available
    if not check_dependencies():
        print("Required dependencies not available")
        print("Please install ffmpeg and vosk: pip install vosk")
        return
    
    # Path to the .ts file
    ts_file = "recordings/deslic/deslic-320111820413-20250330001707.ts"
    
    # Path to the Vosk model
    model_path = "models/vosk-model-small-en-us-0.15"
    
    try:
        # Step 1: Extract audio from the .ts file
        print(f"Extracting audio from {ts_file}")
        wav_path = extract_audio_from_ts(ts_file)
        
        # Step 2: Transcribe the audio
        print(f"Transcribing audio from {wav_path}")
        transcript = transcribe_audio(wav_path, model_path)
        
        # Step 3: Save the transcript
        transcript_path = os.path.splitext(ts_file)[0] + ".manual.transcript.json"
        print(f"Saving transcript to {transcript_path}")
        save_transcript(transcript, transcript_path)
        
        # Step 4: Clean up the WAV file
        print(f"Cleaning up temporary WAV file: {wav_path}")
        os.remove(wav_path)
        
        print(f"Transcription completed successfully")
        
        # Print a sample of the transcript
        print("\nTranscript sample:")
        print(f"Full text: {transcript['text'][:100]}...")
        print("\nSegments:")
        for i, segment in enumerate(transcript['segments'][:3]):
            print(f"  {i+1}. [{segment['start']:.2f}s - {segment['end']:.2f}s]: {segment['text']}")
        
        if len(transcript['segments']) > 3:
            print(f"  ... and {len(transcript['segments']) - 3} more segments")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Example 1: Full process using process_ts_file()")
    print("-" * 50)
    example_full_process()
    
    print("\nExample 2: Step-by-step process")
    print("-" * 50)
    example_step_by_step()
