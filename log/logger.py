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


old_factory = logging.getLogRecordFactory()
app_name = ""


def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.appname = app_name
    return record


def setup_logging(config):
    level = logging.DEBUG if config['DEBUG'] else logging.INFO
    # Our logging routines signal the start and end of the routes,
    # so the Werkzeug defaults aren't required. Keep warnings and above.
    logging.getLogger('werkzeug').setLevel(logging.WARN)

    global app_name
    app_name = config['APPLICATION_NAME']

    root_logger = logging.getLogger()
    logging.setLogRecordFactory(record_factory)
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s [%(appname)s]'
                                  ' (PID %(process)d) Message: %(message)s',
                                  "%Y-%m-%d %H:%M:%S")

    out_handler = logging.StreamHandler(sys.stdout)
    out_handler.addFilter(OutputFilter(False))
    out_handler.setFormatter(formatter)
    root_logger.addHandler(out_handler)

    err_handler = logging.StreamHandler(sys.stderr)
    err_handler.addFilter(OutputFilter(True))
    err_handler.setFormatter(formatter)
    root_logger.addHandler(err_handler)
    root_logger.setLevel(level)
