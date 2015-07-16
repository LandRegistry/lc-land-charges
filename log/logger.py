import logging
import sys


class OutputFilter(logging.Filter):
    def __init__(self, is_error):
        self.is_error = is_error

    def filter(self, record):
        if record.levelno <= logging.INFO:
            return not self.is_error
        else:
            return self.is_error


level = "DEBUG"

root_logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                              "%Y-%m-%d %H:%M:%S")

out_handler = logging.StreamHandler(sys.stdout)
out_handler.addFilter(OutputFilter(False))
out_handler.setFormatter(formatter)
root_logger.addHandler(out_handler)

err_handler = logging.StreamHandler(sys.stderr)
err_handler.addFilter(OutputFilter(True))
err_handler.setFormatter(formatter)
root_logger.addHandler(err_handler)

logger = logging.getLogger("logger")
logger.setLevel(getattr(logging, level.upper(), None))