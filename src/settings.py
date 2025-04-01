from utils import *

config = None

def init():
    global config
    config = load_config("config")