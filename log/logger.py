import logging
import sys
import inspect


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
    record.file = inspect.stack()[5][1]
    record.line = inspect.stack()[5][2]
    record.method = inspect.stack()[5][3]
    return record


def setup_logging(config):
    level = logging.DEBUG if config['DEBUG'] else logging.INFO
    # Our logging routines signal the start and end of the routes,
    # so the Werkzeug defaults aren't required. Keep warnings and above.
    logging.getLogger('werkzeug').setLevel(logging.WARN)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

    global app_name
    app_name = config['APPLICATION_NAME']

    root_logger = logging.getLogger()
    logging.setLogRecordFactory(record_factory)
    formatter = logging.Formatter('%(levelname)s %(asctime)s.%(msecs)03d [%(appname)s] %(file)s #%(line)s %(method)s'
                                  ' %(message)s',
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
