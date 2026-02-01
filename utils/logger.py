from loguru import logger
import sys

def setup_logger():
    logger.remove()
    logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", level="DEBUG")
    logger.add("aether_fin.log", rotation="10 MB", level="DEBUG")

setup_logger()
