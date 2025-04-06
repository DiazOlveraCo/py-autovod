from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> | <level>{message}</level>",
    colorize=True,
)