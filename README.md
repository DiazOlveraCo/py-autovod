# AutoVOD.py

A Python implementation of [autovod](https://github.com/jenslys/AutoVOD) with some extra features.

## Features
- ( :heavy_check_mark: ) Auto download livestreams (Twitch.tv, Kick.tv, Youtube Live) from multiple streamers concurrently
- ( :heavy_check_mark: ) Audio transcription with timestamps for downloaded streams
- ( :x: ) Auto upload to RClone, YouTube, and more
- ( :x: ) Smart AI video clipping
- ( :x: ) Youtube shorts formatting
- ( :x: ) Archive both video and chat logs
- ( :x: ) Platform independent and Docker supported

## Installation

Manually install ffmpeg, streamlink, jq, pm2, YoutubeUploader. Alternatively, you can do the installation automatically with `install.sh`

For the transcription feature, you'll also need:
- ffmpeg (for audio extraction)
- vosk (for speech recognition): `pip install vosk`
- A Vosk model (download from [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models))

See [TRANSCRIPTION.md](TRANSCRIPTION.md) for detailed instructions on setting up and using the transcription feature.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the streamers you want to monitor in `config.ini`:
   ```ini
   [streamers]
   streamers = streamer1, streamer2, streamer3
   ```

3. Create a configuration file for each streamer (e.g., `streamer1.ini`).

4. Run the application:
   ```bash
   python src/main.py
   ```

## Transcription

AutoVOD now includes functionality to automatically transcribe the audio from downloaded stream recordings. The transcription is performed using the [Vosk](https://alphacephei.com/vosk/) speech recognition toolkit.

To use this feature:
1. Install the required dependencies: `pip install vosk`
2. Download a Vosk model from [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
3. Configure the transcription settings in `config.ini`

For more details, see [TRANSCRIPTION.md](TRANSCRIPTION.md).

## Contribution

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This software is provided as-is with no warranty. Use at your own risk.
