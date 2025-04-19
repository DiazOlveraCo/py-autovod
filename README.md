# AutoVOD.py
[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Issues](https://img.shields.io/github/issues/0jc1/py-autovod.svg)](https://github.com/0jc1/py-autovod/issues)

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

Manually install ffmpeg and streamlink. Alternatively, you can do the installation automatically with `install.sh`.

## Setup

1. Python 3.9+ is required. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the streamers you want to monitor in `config.ini`:
   ```ini
   [streamers]
   streamers = streamer1, streamer2, streamer3
   ```

Create a configuration file for each streamer where the file name is the streamer's username.

3. Copy the `.env.example` file to a new file called `.env`. Fill in the .env file with your API keys.

4. Run the program:
   ```bash
   python3 src/main.py
   ```

## Transcription

Audio transcription is done with OpenAI's Whisper ASR. This feature can be configured in `config.ini`

## Contribution

Contributors are welcome! Please feel free to submit a PR or issue.

## Credits

[@jenslys](https://github.com/jenslys) - creating the original [autovod](https://github.com/jenslys/AutoVOD)  

[@msylvester](https://github.com/msylvester) - their work on [clipception](https://github.com/msylvester/Clipception)
