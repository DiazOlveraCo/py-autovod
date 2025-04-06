import os
import subprocess
from typing import List, Optional, Tuple, Dict
from logger import logger
import configparser

def run_command(
    cmd: List[str],
    stdout: Optional[int] = subprocess.DEVNULL,
    stderr: Optional[int] = subprocess.DEVNULL,
) -> subprocess.CompletedProcess:
    if not cmd:
        logger.error("Command list is empty")
        return subprocess.CompletedProcess([], -1)
        
    logger.debug(f"Executing: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e}")
        return subprocess.CompletedProcess(cmd, -1)


def is_docker() -> bool:
    return os.path.exists("/.dockerenv")


def determine_source(stream_source: str, streamer_name: str) -> Optional[str]:
    if not stream_source or not streamer_name:
        logger.error("Stream source and streamer name cannot be empty")
        return None
        
    sources: Dict[str, str] = {
        "twitch": f"twitch.tv/{streamer_name}",
        "kick": f"kick.com/{streamer_name}",
        "youtube": f"youtube.com/@{streamer_name}/live",
    }
    return sources.get(stream_source.lower())


def check_stream_live(url: str) -> bool:
    # TODO this takes many seconds, find a faster method
    result = run_command(["streamlink", url])
    return result.returncode == 0


def get_size(path: str) -> float:
    if not os.path.exists(path):
        logger.warning(f"Path does not exist: {path}")
        return 0.0
        
    bytes_total = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(path)
        for filename in filenames
    )
    return bytes_total / 1_000_000  # Convert to MB


def fetch_metadata(api_url: str, streamer_name: str) -> Tuple[str, str]:
    # TODO: Implement this function properly
    # streamlink --json twitch.tv/bobross | jq .metadata
    if not api_url:
        return None, None

    # Placeholder for actual implementation
    return None, None


def load_config(config_name: str) -> Optional[configparser.ConfigParser]:
    config = configparser.ConfigParser()
    config_file = f"{config_name}.ini"

    if not os.path.isfile(config_file):
        logger.warning(f"No config file found for {config_name}")
        return None

    config.read(config_file)
    logger.info(f"Loaded configuration from {config_file}")
    return config
