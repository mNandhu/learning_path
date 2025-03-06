import logging
import sys
from pathlib import Path
import colorlog


def setup_logger():
    """Configure logging to both console and file with proper formatting."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Set up logging format with colored output for console
    log_format = "%(asctime)s - %(log_color)s%(levelname)s - %(module)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create formatter for colored console output
    console_formatter = colorlog.ColoredFormatter(
        log_format,
        datefmt=date_format,
        log_colors={
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    # Create the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to avoid duplicate logs
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # File handler for persistent logs
    file_handler = logging.FileHandler(logs_dir / "learning_path.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # More verbose in the log file
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(module)s - %(message)s", date_format
        )
    )

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Initialize and export the logger
logger = setup_logger()
