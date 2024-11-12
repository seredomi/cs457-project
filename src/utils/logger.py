import logging
import sys
from pathlib import Path


def setup_logger(log_file: str) -> logging.Logger:
    """
    Sets up a custom logger that writes to both file and console

    Args:
        log_file (str): Path to the log file

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(log_file)  # Use log_file as logger name
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Prevent adding handlers multiple times
    if not logger.handlers:
        # File handler - DEBUG and up
        file_handler = logging.FileHandler(log_dir / log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Console handler - INFO and up
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
