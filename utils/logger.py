from loguru import logger
import sys
import os

def setup_logger():
    logger.remove()
    # sys.stderr is None when running as a windowed .exe (PyInstaller console=False)
    if sys.stderr is not None:
        logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>", level="DEBUG")
    # Log file goes next to the executable (or current dir)
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = "."
    logger.add(os.path.join(log_dir, "aether_fin.log"), rotation="10 MB", level="DEBUG")

setup_logger()
