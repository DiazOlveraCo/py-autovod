import os
import sys
import time
import json
import subprocess
import argparse
import requests
import configparser
from loguru import logger
from datetime import datetime
from typing import List, Optional
from settings import RETRY_DELAY

def run_command(cmd: List[str], stdout: Optional[int] = subprocess.DEVNULL, stderr: Optional[int] = subprocess.DEVNULL) -> subprocess.CompletedProcess:
    print(f"Executing: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, stdout=stdout, stderr=stderr) 
    except subprocess.CalledProcessError as e:
        print("Command failed with error:", e)
        return -1

# Configure logger to include timestamp 
logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> <level>{message}</level>",
    colorize=True
)

def load_config(streamer_name):
    config = configparser.ConfigParser()
    
    config_file = f"{streamer_name}.ini"
    found_file = None
    
    if os.path.isfile(config_file):
        found_file = config_file
    
    if not found_file:
        logger.error("No config file found")
        sys.exit(1)

    config.read(found_file)
    logger.info(f"Loaded configuration from {found_file}")
    return config

def is_docker():
    return os.path.exists('/.dockerenv')

def determine_source(stream_source, streamer_name):
    sources = {
        "twitch": f"twitch.tv/{streamer_name}",
        "kick": f"kick.com/{streamer_name}",
        "youtube": f"youtube.com/@{streamer_name}/live"
    }
    return sources.get(stream_source.lower(), None)

def check_stream_live(url):
    result = run_command(["streamlink", url])
    return result.returncode == 0

# TODO fix this function
def fetch_metadata(api_url, streamer_name):
    if not api_url:
        return None, None
        
    response = requests.get(f"{api_url}/info/{streamer_name}")
    if response.status_code != 200:
        return None, None

    data = response.json()
    return data.get("stream_title", ""), data.get("stream_game", "")

def process_video(stream_source_url, config, streamer_name, video_title, video_description):
    upload_service = config['upload']['service'].lower()
    quality = config['streamlink']['quality']
    date_str = datetime.now().strftime("%d-%m-%Y")
    
    if upload_service == "youtube":
        metadata = {
            "title": video_title or config['youtube']['title'].format(
                streamer_name=streamer_name,
                date=date_str
            ),
            "privacyStatus": config['youtube']['visibility'],
            "description": video_description or config['youtube']['description'],
            "playlistTitles": [config['youtube']['playlist'].format(
                streamer_name=streamer_name
            )]
        }

        # TODO make this work on windows
        with open(f"/tmp/input.json", "w") as file:
            json.dump(metadata, file)

        result = run_command(["streamlink", "-o", "stream.ts", stream_source_url, quality])
        return result.returncode == 0 

    elif upload_service == "rclone":
        remote = config['rclone']['remote']
        if not remote:
            logger.error("Rclone remote not configured")
            return False
            
        filename = config['rclone']['filename'].format(
            streamer_name=streamer_name,
            date=date_str
        )
        fileext = config['rclone']['fileext']
        temp_file = f"{filename}.{fileext}"
        
        result = run_command(["streamlink", stream_source_url, "-o", temp_file, quality])
        
        if result.returncode == 0 and config.getboolean('encoding', 're_encode'):
            logger.info("Re-encoding video...")
            codec = config['encoding']['codec']
            crf = config['encoding']['crf']
            preset = config['encoding']['preset']
            
            encoded_file = f"encoded_{temp_file}"
            result = run_command([
                "ffmpeg", "-i", temp_file,
                "-c:v", codec,
                "-crf", crf,
                "-preset", preset,
                encoded_file
            ])
            
            if result.returncode == 0:
                os.remove(temp_file)
                temp_file = encoded_file
            else:
                logger.error("Re-encoding failed")
                if not config.getboolean('upload', 'save_on_fail'):
                    os.remove(temp_file)
                return False
        
        if result.returncode == 0:
            remote_path = config['rclone']['directory'].strip('/')
            if remote_path:
                remote_path = f"{remote_path}/{temp_file}"
            else:
                remote_path = temp_file
                
            result = run_command(["rclone", "copyto", temp_file, f"{remote}:{remote_path}"])
            
            if not config.getboolean('upload', 'save_on_fail'):
                os.remove(temp_file)
                
            return result.returncode == 0
            
        return False

    elif upload_service == "local":
        filename = config['local']['filename'].format(
            streamer_name=streamer_name,
            date=date_str
        )
        fileext = config['local']['extension']
        output_file = f"{filename}.{fileext}"
        
        result = run_command(["streamlink", stream_source_url, "-o", output_file, quality])
        
        if result.returncode == 0 and config.getboolean('encoding', 're_encode'):
            logger.info("Re-encoding video...")
            codec = config['encoding']['codec']
            crf = config['encoding']['crf']
            preset = config['encoding']['preset']
            
            encoded_file = f"encoded_{output_file}"
            result = run_command([
                "ffmpeg", "-i", output_file,
                "-c:v", codec,
                "-crf", crf,
                "-preset", preset,
                encoded_file
            ])
            
            if result.returncode == 0:
                os.remove(output_file)
                os.rename(encoded_file, output_file)
            else:
                logger.error("Re-encoding failed")
                if not config.getboolean('upload', 'save_on_fail'):
                    os.remove(output_file)
                return False
                
        return result.returncode == 0

    return False

def main():
    logger.info("Starting AutoVOD v1.0.0")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", required=not is_docker(), help="Streamer name")
    args = parser.parse_args()
    
    streamer_name = args.name
    logger.info(f"Selected streamer: {streamer_name}")

    config = load_config(streamer_name)
    stream_source = config['source']['stream_source']
    stream_source_url = determine_source(stream_source, streamer_name)

    if not stream_source_url:
        logger.error(f"Unknown stream source: {stream_source}")
        sys.exit(1)

    while True:
        if check_stream_live(stream_source_url):
            logger.info("Stream is live")
            
            video_title = None
            video_description = None
            
            if config.getboolean('source', 'api_calls'):
                video_title, video_description = fetch_metadata(
                    config['source']['api_url'],
                    streamer_name
                )

            upload_success = process_video(
                stream_source_url,
                config,
                streamer_name,
                video_title,
                video_description
            )

            if upload_success:
                logger.success("Stream uploaded successfully")
            else:
                logger.error("Stream upload failed")

        else:
            logger.info(f"Stream is offline. Retrying in {RETRY_DELAY} seconds...")

        time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    main()
