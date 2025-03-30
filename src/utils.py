import os
import subprocess
from typing import List, Optional, Tuple
from loguru import logger

def run_command(
    cmd: List[str],
    stdout: Optional[int] = subprocess.DEVNULL,
    stderr: Optional[int] = subprocess.DEVNULL,
) -> subprocess.CompletedProcess:
    """Execute a command and return the result."""
    logger.debug(f"Executing: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e}")
        return subprocess.CompletedProcess(cmd, -1)

def is_docker() -> bool:
    """Check if running inside a Docker container."""
    return os.path.exists("/.dockerenv")

def determine_source(stream_source: str, streamer_name: str) -> str:
    """Determine the stream source URL based on the source type and streamer name."""
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

def fetch_metadata(api_url: str, streamer_name: str) -> Tuple[str, str]:
    # TODO: Implement this function properly
    # streamlink --json twitch.tv/bobross | jq .metadata
    if not api_url:
        return None, None
    
    # Placeholder for actual implementation
    return None, None

def load_config(streamer_name: str):
    """Load configuration for a specific streamer."""
    import configparser
    
    config = configparser.ConfigParser()
    config_file = f"{streamer_name}.ini"
    
    if not os.path.isfile(config_file):
        logger.error(f"No config file found for {streamer_name}")
        return None
    
    config.read(config_file)
    logger.info(f"Loaded configuration from {config_file}")
    return config

def load_main_config():
    """Load the main configuration file."""
    import configparser
    
    config = configparser.ConfigParser()
    config_file = "config.ini"
    
    if not os.path.isfile(config_file):
        logger.error("Main config file (config.ini) not found")
        return None
    
    config.read(config_file)
    logger.info(f"Loaded main configuration from {config_file}")
    return config

def get_version():
    """Get the current version of AutoVOD from config.ini."""
    config = load_main_config()
    if not config:
        logger.error("Failed to load configuration, cannot determine version")
        return "unknown"
    
    try:
        return config.get("general", "version")
    except (configparser.NoSectionError, configparser.NoOptionError):
        logger.error("Version information not found in config.ini")
        return "unknown"
