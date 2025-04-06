from loguru import logger
import sys

logger.remove()
logger.add(
    sys.stderr,
    format="<green>[{time:HH:mm:ss}]</green> | <level>{message}</level>",
    colorize=True,
)

# logger.add(
#     log_file,
#     rotation="10 MB",
#     retention="1 week",
#     format="[{time:YYYY-MM-DD HH:mm:ss}] | {level} | {message}",
# )
