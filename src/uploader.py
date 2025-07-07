import os
from utils import run_command

YOUTUBE_UPLOADER_PATH = "/root/youtubeuploader/youtubeuploader"

def upload_youtube(filename: str) -> None:
    if not os.path.isfile(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    command = [YOUTUBE_UPLOADER_PATH, "-filename", filename]

    result = run_command(command)

    if result.returncode != 0:
        raise RuntimeError("youtubeuploader failed to upload the file")
    else:
        return None