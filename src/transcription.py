import os
import json
import wave
import subprocess
from typing import Dict, Optional, Tuple
from loguru import logger

try:
    import vosk

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("Vosk library not found. Transcription will not be available.")


def check_dependencies() -> bool:
    """Check if all required dependencies are available."""
    # Check for ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        ffmpeg_available = result.returncode == 0
    except FileNotFoundError:
        ffmpeg_available = False
        logger.warning("ffmpeg not found. Audio extraction will not be available.")

    return ffmpeg_available and VOSK_AVAILABLE


def extract_audio_from_ts(
    ts_file_path: str, output_wav_path: Optional[str] = None
) -> str:
    """
    Extract audio from a .ts file using ffmpeg.

    Args:
        ts_file_path: Path to the .ts file
        output_wav_path: Optional path for the output WAV file. If not provided,
                         it will be created alongside the .ts file.

    Returns:
        Path to the extracted WAV file
    """
    if not os.path.exists(ts_file_path):
        raise FileNotFoundError(f"TS file not found: {ts_file_path}")

    if output_wav_path is None:
        # Create WAV file path alongside the TS file
        output_wav_path = os.path.splitext(ts_file_path)[0] + ".wav"

    logger.info(f"Extracting audio from {ts_file_path} to {output_wav_path}")

    # Use ffmpeg to extract audio to WAV format (PCM 16-bit)
    cmd = [
        "ffmpeg",
        "-i",
        ts_file_path,
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",  # PCM 16-bit
        "-ar",
        "16000",  # 16kHz sample rate (good for speech recognition)
        "-ac",
        "1",  # Mono
        "-y",  # Overwrite output file if it exists
        output_wav_path,
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8", errors="replace")
            logger.error(f"Failed to extract audio: {error_msg}")
            raise RuntimeError(f"Failed to extract audio: {error_msg}")

        return output_wav_path

    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise


def transcribe_audio(audio_file_path: str, model_name: str) -> Dict:
    """
    Transcribe audio file using Vosk.

    Args:
        audio_file_path: Path to the audio file (WAV format)
        model_name:

    Returns:
        Dictionary containing the transcription with timestamps
    """
    if not VOSK_AVAILABLE:
        raise ImportError(
            "Vosk library is not available. Please install it with 'pip install vosk'"
        )

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    logger.info(f"Transcribing audio file: {audio_file_path}")

    # For a smaller download size, use model = Model(model_name="vosk-model-small-en-us-0.15")
    model = vosk.Model(model_name=model_name)

    # Open the audio file
    wf = wave.open(audio_file_path, "rb")

    # Check if the audio format is compatible with Vosk
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        logger.error("Audio file must be WAV format mono PCM.")
        raise ValueError("Audio file must be WAV format mono PCM.")

    # Create recognizer
    rec = vosk.KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # Enable word timestamps

    # Process audio in chunks
    results = []
    while True:
        data = wf.readframes(4000)  # Read 4000 frames at a time
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            if "result" in part_result:
                results.extend(part_result["result"])

    # Get final result
    part_result = json.loads(rec.FinalResult())
    if "result" in part_result:
        results.extend(part_result["result"])

    # Close the audio file
    wf.close()

    # Format the results
    transcript = {"segments": [], "text": ""}

    current_segment = {"start": 0, "end": 0, "text": ""}

    full_text = []

    for word in results:
        print(word)
        if "start" in word and "end" in word and "word" in word:
            # If this word is more than 2 seconds after the last one, start a new segment
            if (
                current_segment["text"]
                and (word["start"] - current_segment["end"]) > 2.0
            ):
                transcript["segments"].append(current_segment)
                current_segment = {
                    "start": word["start"],
                    "end": word["end"],
                    "text": word["word"],
                }
            else:
                if not current_segment["text"]:
                    current_segment["start"] = word["start"]
                current_segment["end"] = word["end"]
                current_segment["text"] += (
                    " " + word["word"] if current_segment["text"] else word["word"]
                )

            full_text.append(word["word"])

    # Add the last segment if it exists
    if current_segment["text"]:
        transcript["segments"].append(current_segment)

    transcript["text"] = " ".join(full_text)

    return transcript


def save_transcript(transcript: Dict, output_path: str) -> None:
    """
    Save the transcript to a file.

    Args:
        transcript: Dictionary containing the transcription
        output_path: Path to save the transcript
    """
    logger.info(f"Saving transcript to {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)


def process_ts_file(
    ts_file_path: str, model_name: str, cleanup_wav: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Process a .ts file to generate a transcript.

    Args:
        ts_file_path: Path to the .ts file
        model_path: Path to the Vosk model directory
        cleanup_wav: Whether to delete the intermediate WAV file

    Returns:
        Tuple of (success, transcript_path)
    """
    if not check_dependencies():
        logger.error("Required dependencies not available for transcription")
        return False, None

    transcript_path = os.path.splitext(ts_file_path)[0] + ".transcript.json"
    wav_path = None

    try:
        # Extract audio
        wav_path = extract_audio_from_ts(ts_file_path)

        # Transcribe audio
        transcript = transcribe_audio(wav_path, model_name)

        # Save transcript
        save_transcript(transcript, transcript_path)

        logger.success(f"Successfully transcribed {ts_file_path}")
        return True, transcript_path

    except Exception as e:
        logger.error(f"Error processing {ts_file_path} for transcription: {str(e)}")
        return False, None

    finally:
        # Clean up the WAV file if requested
        if cleanup_wav and wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
                logger.debug(f"Removed temporary WAV file: {wav_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary WAV file: {str(e)}")
