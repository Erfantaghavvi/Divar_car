import logging
from datetime import datetime

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Constants controlling log frequency (number of items between logs)
HAMRAH_LOG_INTERVAL = 50  # Log every 50 processed items for Hamrah Mechanic
Z4CAR_LOG_INTERVAL = 50   # Log every 50 processed items for Z4Car

# Flag to enable very verbose logging in scrapers or other modules
VERBOSE_LOGGING = False

def log_progress(message: str, level: str = "info") -> None:
    """Light-weight helper used by various modules to log incremental progress.

    Parameters
    ----------
    message : str
        Message to log.
    level : str, optional
        Logging level as a string ("info", "warning", "error", "debug"). Default is "info".
    """
    level = level.lower()
    timestamp = datetime.now().strftime("%H:%M:%S")

    if level == "debug":
        logging.debug(message)
    elif level == "warning":
        logging.warning(message)
    elif level == "error":
        logging.error(message)
    else:
        logging.info(message)

    # Always print to console as well for immediate feedback (can be disabled if needed)
    print(f"[{timestamp}] {message}")