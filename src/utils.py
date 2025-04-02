import os
import subprocess
from typing import List, Optional, Tuple
from loguru import logger
import configparser


def run_command(
    cmd: List[str],
    stdout: Optional[int] = subprocess.DEVNULL,
    stderr: Optional[int] = subprocess.DEVNULL,
) -> subprocess.CompletedProcess:
    """Execute a command and return the result."""
    logger.debug(f"Executing: {' '.join(cmd)}")
    assert len(cmd) > 0, "Cmd list empty"
    try:
        return subprocess.run(cmd, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e}")
        return subprocess.CompletedProcess(cmd, -1)


def is_docker() -> bool:
    return os.path.exists("/.dockerenv")


def determine_source(stream_source: str, streamer_name: str) -> str:
    assert stream_source and streamer_name, "Strings shouldn't be empty"
    sources = {
        "twitch": f"twitch.tv/{streamer_name}",
        "kick": f"kick.com/{streamer_name}",
        "youtube": f"youtube.com/@{streamer_name}/live",
    }
    return sources.get(stream_source.lower(), None)


def check_stream_live(url: str) -> bool:
    """Check if a stream is currently live."""
    # TODO this takes many seconds, find a faster method
    result = run_command(["streamlink", url])
    return result.returncode == 0

def get_size(path : str) -> int:
    """returns the file sizes in MB of files in a dir"""
    b =  sum( os.path.getsize(os.path.join(dirpath,filename)) for dirpath, dirnames, filenames in os.walk( path ) for filename in filenames )
    return b/1000000

def fetch_metadata(api_url: str, streamer_name: str) -> Tuple[str, str]:
    # TODO: Implement this function properly
    # streamlink --json twitch.tv/bobross | jq .metadata
    if not api_url:
        return None, None

    # Placeholder for actual implementation
    return None, None

def load_config(config_name: str):
    config = configparser.ConfigParser()
    config_file = f"{config_name}.ini"
    
    if not os.path.isfile(config_file):
        logger.error(f"No config file found for {config_name}")
        return None

    config.read(config_file)
    logger.info(f"Loaded configuration from {config_file}")
    return config