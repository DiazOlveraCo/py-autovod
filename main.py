import argparse, subprocess, json, time, sys, os
import requests
from loguru import logger
from datetime import datetime

# Configure logger to include timestamp in the same format as before
logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> <level>{message}</level>",
    colorize=True
)

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def get_current_date():
    return datetime.now().strftime("%d-%m-%y")

def is_docker():
    return os.path.exists('/.dockerenv')

def load_config(streamer_name):
    config_file = f"{streamer_name}.config"
    if not os.path.isfile(config_file):
        logger.error("Config file is missing")
        sys.exit(1)

    with open(config_file, "r") as file:
        return file.read()

def determine_source(stream_source, streamer_name):
    sources = {
        "twitch": f"twitch.tv/{streamer_name}",
        "kick": f"kick.com/{streamer_name}",
        "youtube": f"youtube.com/@{streamer_name}/live"
    }
    return sources.get(stream_source, None)

def check_stream_live(url):
    result = subprocess.run(["streamlink", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0

def fetch_metadata(api_url, streamer_name):
    response = requests.get(f"{api_url}/info/{streamer_name}")
    if response.status_code != 200:
        return None, None

    data = response.json()
    return data.get("stream_title", ""), data.get("stream_game", "")

def process_video(stream_source_url, upload_service, video_title, video_description, video_playlist):
    if upload_service == "youtube":
        metadata = {
            "title": video_title,
            "privacyStatus": "public",
            "description": video_description,
            "playlistTitles": [video_playlist]
        }
        with open(f"/tmp/input.json", "w") as file:
            json.dump(metadata, file)

        # streamlink 
        # ffmpeg -i input.ts -c copy output.mp4

        result = subprocess.run(["streamlink", "-o","stream.ts", stream_source_url, "best"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0

    elif upload_service == "rclone":
        temp_file = "stream_temp.mp4"
        result = subprocess.run(["streamlink", stream_source_url, "-o", temp_file, "best"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        #if result.returncode == 0:
        #   return subprocess.run(["rclone", "copyto", temp_file, f"remote:{temp_file}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        return False

    return False

def main():
    logger.info("Starting AutoVOD")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", required=not is_docker(), help="Streamer name")
    args = parser.parse_args()
    
    streamer_name = args.name
    logger.info(f"Selected streamer: {streamer_name}")

    # config_content = load_config(streamer_name)
    stream_source = "twitch"  # Extract this from the config content dynamically
    stream_source_url = determine_source(stream_source, streamer_name)

    if not stream_source_url:
        logger.error(f"Unknown stream source: {stream_source}")
        sys.exit(1)

    while True:
        if check_stream_live(stream_source_url):
            logger.info("Stream is live")
            video_title, video_description = None, None #fetch_metadata("https://twitch.tv/", streamer_name)

            if not video_title:
                video_title = "Default Title"
            if not video_description:
                video_description = "Default Description"

            upload_success = process_video(stream_source_url, "rclone", video_title, video_description, "Gaming")

            if upload_success:
                logger.success("Stream uploaded successfully")
            else:
                logger.error("Stream upload failed")

        else:
            logger.info("Stream is offline. Retrying in 60 seconds...")

        time.sleep(10)

if __name__ == "__main__":
    main()
