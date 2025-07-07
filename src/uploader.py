import os
import platform
from utils import run_command

YOUTUBE_UPLOADER_LINUX = "/root/youtubeuploader/youtubeuploader"
YOUTUBE_UPLOADER_WINDOWS = "C:\\youtubeuploader\\youtubeuploader.exe"  

def upload_youtube(filename: str) -> None:
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    system = platform.system()
    
    if system == "Windows":
        uploader_path = YOUTUBE_UPLOADER_WINDOWS
        filename = os.path.normpath(filename)
    else:
        uploader_path = YOUTUBE_UPLOADER_LINUX

    command = [uploader_path, "-filename", f"'{filename}'"]
    result = run_command(command)

    if result.returncode != 0:
        raise RuntimeError("youtubeuploader failed to upload the file")
