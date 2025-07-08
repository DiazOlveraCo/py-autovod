from loguru import logger
import sys

DEBUG = True
LOGFILE = False


def debug_filter(record):
    return DEBUG or record["level"].name != "debug"


logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> | <level>{message}</level>",
    filter=debug_filter,
    colorize=True,
)

if LOGFILE: 
    logger.add(
        "app.log",
        rotation="10 MB",
        retention="1 week",
        format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}",
    )