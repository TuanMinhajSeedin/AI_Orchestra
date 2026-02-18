import logging
import os


def _configure_logging() -> None:
    """
    Configure root logger to print to console and write to logs/runing_logs.log.

    Format: [%(asctime)s]: %(message)s
    Level:  INFO
    """

    # Avoid re-configuring if handlers already exist (e.g. on reload).
    if logging.getLogger().handlers:
        return

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(root_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_path = os.path.join(logs_dir, "runing_logs.log")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    console_handler = logging.StreamHandler()

    # Use the required basicConfig signature so logs go both to file and console
    # with the requested format.
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s]: %(message)s',
        handlers=[file_handler, console_handler],
    )


_configure_logging()


