import logging
import colorlog
from logging.handlers import SysLogHandler
import os

PAPERTRIAL_HOST = os.getenv("PAPERTRIAL_HOST")
PAPERTRIAL_PORT = os.getenv("PAPERTRIAL_PORT")

def setup_logger():
    logger = logging.getLogger()
    if logger.handlers:
        return logger

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "blue",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
    )
    paper_trial_handler = SysLogHandler(address=(PAPERTRIAL_HOST, int(PAPERTRIAL_PORT)))

    logger.addHandler(handler)
    logger.addHandler(paper_trial_handler)
    logger.setLevel(logging.DEBUG)  # Set this to the desired level

    return logger
