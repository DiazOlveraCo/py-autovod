from utils import load_config
import configparser
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPEN_ROUTER_KEY")

# Check for OpenRouter API key
if not API_KEY:
    print("Error: OPEN_ROUTER_KEY environment variable is not set")
    raise ValueError("Please set it with: export OPEN_ROUTER_KEY='your_key_here'")

config: configparser.ConfigParser = load_config("config")