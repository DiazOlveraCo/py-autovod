# Audio Transcription for AutoVOD

This document explains how to use the audio transcription feature in AutoVOD.

## Overview

AutoVOD now includes functionality to automatically transcribe the audio from downloaded stream recordings (.ts files). The transcription is performed using the [Vosk](https://alphacephei.com/vosk/) speech recognition toolkit, which is an offline speech recognition system that doesn't require an internet connection or API keys.

## Requirements

To use the transcription feature, you need:

1. **ffmpeg**: Used to extract audio from video files
   - Install on Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - Install on macOS: `brew install ffmpeg`
   - Install on Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

2. **Vosk**: Speech recognition toolkit
   - Install with pip: `pip install vosk`

3. **Vosk Model**: A speech recognition model for your language
   - Download from [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
   - Recommended models:
     - Small English model (good for testing): `vosk-model-small-en-us-0.15` (~40MB)
     - Standard English model (better accuracy): `vosk-model-en-us-0.22` (~1.8GB)

## Configuration

The transcription feature is configured in the `config.ini` file:

```ini
[transcription]
# Enable or disable automatic transcription of downloaded streams
enabled = true

# Path to the Vosk model directory
# Download models from https://alphacephei.com/vosk/models
model_path = models/vosk-model-small-en-us-0.15

# Clean up temporary WAV files after transcription
cleanup_wav = true
```

### Configuration Options

- `enabled`: Set to `true` to enable automatic transcription of downloaded streams, or `false` to disable it.
- `model_path`: Path to the Vosk model directory. You need to download a model from the Vosk website and extract it to this location.
- `cleanup_wav`: Set to `true` to delete the temporary WAV files after transcription, or `false` to keep them.

## Setting Up

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Download a Vosk model:
   ```bash
   # Create a models directory
   mkdir -p models
   
   # Download a small English model (for testing)
   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   
   # Extract the model
   unzip vosk-model-small-en-us-0.15.zip -d models/
   ```

3. Update the `config.ini` file with the correct model path.

## Usage

### Automatic Transcription

When the transcription feature is enabled in the config, AutoVOD will automatically transcribe the audio from downloaded streams. The transcription will be saved alongside the .ts file with the extension `.transcript.json`.

### Manual Transcription

You can also manually transcribe existing .ts files using the `transcribe_file.py` script:

```bash
python src/transcribe_file.py recordings/streamer/video.ts
```

Options:
- `-m, --model`: Specify a different model path than the one in the config
- `--keep-wav`: Keep the intermediate WAV file (useful for debugging)

Example:
```bash
python src/transcribe_file.py recordings/deslic/deslic-320111820413-20250330001707.ts --model models/vosk-model-en-us-0.22
```

## Transcript Format

The transcription is saved as a JSON file with the following structure:

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 5.34,
      "text": "hello everyone welcome to the stream"
    },
    {
      "start": 7.2,
      "end": 12.5,
      "text": "today we're going to be talking about..."
    },
    ...
  ],
  "text": "hello everyone welcome to the stream today we're going to be talking about..."
}
```

The transcript includes:
- `segments`: An array of segments, each with a start time, end time, and text
- `text`: The full transcript text

## Troubleshooting

### Missing Dependencies

If you see errors about missing dependencies, make sure you have installed ffmpeg and the Vosk library:

```bash
pip install vosk
```

### Model Not Found

If you see errors about the model not being found, make sure you have downloaded a Vosk model and updated the `model_path` in the config.ini file.

### Transcription Quality

The quality of the transcription depends on the model used. For better results:

1. Use a larger model (e.g., `vosk-model-en-us-0.22`)
2. Ensure the audio has good quality (clear speech, minimal background noise)
3. Use a model that matches the language of the audio

## Performance Considerations

Speech recognition is a resource-intensive process. The time it takes to transcribe a file depends on:

1. The length of the audio
2. The size of the model
3. Your computer's CPU speed

For long recordings, the transcription process may take a significant amount of time. Consider using a smaller model if performance is an issue.
