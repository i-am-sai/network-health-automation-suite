import logging  # Python's built-in logging library.
from pathlib import Path
from datetime import datetime

# Networking/reports/   
reports_dir = Path("reports/logs")
reports_dir.mkdir(parents=True, exist_ok=True)

# Networking/reports/test.log
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = reports_dir / f"test_{timestamp}.log"

logger = logging.getLogger("NetworkHealthCheck")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(log_file, mode="w")

    formatter = logging.Formatter(
        "%(asctime)s || %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)






