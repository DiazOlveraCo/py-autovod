# AutoVOD.py

A Python implementation of [autovod](https://github.com/jenslys/AutoVOD) with some extra features.

## Features
- ( :heavy_check_mark: ) Auto download livestreams (Twitch.tv, Kick.tv, Youtube Live) from multiple streamers concurrently
- ( :heavy_check_mark: ) Audio transcription with timestamps 
- ( :x: ) Auto upload to RClone, YouTube, and more
- ( :x: ) Smart AI video clipping
- ( :x: ) Youtube shorts formatting
- ( :x: ) Archive both video and chat logs
- ( :x: ) Platform independent and Docker supported

## Installation

Manually install ffmpeg, streamlink, jq, pm2, YoutubeUploader. Alternatively, you can do the installation automatically with `install.sh`

## Setup

1. Install the packages:
   ```bash
   apt install ffmpeg streamlink jq pm2
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the streamers you want to monitor in `config.ini`:
   ```ini
   [streamers]
   streamers = streamer1, streamer2, streamer3
   ```

4. Create a configuration file for each streamer (e.g., `streamer1.ini`).

5. Run the application:
   ```bash
   python src/main.py
   ```

## Transcription

Transcription is performed using the [Vosk](https://alphacephei.com/vosk/) speech recognition toolkit.

To use this feature:
1. Download a Vosk model from [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)
2. Configure the transcription settings in `config.ini`

For more details, see [TRANSCRIPTION.md](TRANSCRIPTION.md).

## Contribution

Contributors are welcome! Please feel free to submit a PR or issue.

## Disclaimer

This software is provided as-is with no warranty. Use at your own risk.
