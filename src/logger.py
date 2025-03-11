import logging
import sys
from pathlib import Path
import colorlog


def setup_logger(name=None):
    """Configure logging to both console and file with proper formatting.

    Args:
        name: Optional name for the logger. If None, returns the root logger.

    Returns:
        A configured logger instance
    """
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

    # Create or get the logger
    if name and name != "__main__":
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if not logger.handlers:
        # Only add handlers if this logger doesn't have any
        # For named loggers, propagate to the root logger which has the handlers
        if name:
            logger.propagate = True
        else:
            # This is the root logger, add the handlers
            # Console handler with colored output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)

            # File handler for persistent logs
            file_handler = logging.FileHandler(
                logs_dir / "learning_path.log", encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)  # More verbose in the log file
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
                    date_format,
                )
            )

            # Add handlers to logger
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)

    return logger


def get_logger(name=None):
    """Get a configured logger instance.

    Args:
        name: Name for the logger, typically the module name

    Returns:
        A configured logger instance
    """
    return setup_logger(name)
