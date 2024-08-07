import logging
import colorlog


def setup_logger(logger_name):
    logger = colorlog.getLogger(logger_name)
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

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)  # Set this to the desired level

    return logger
