import logging
import sys
import inspect


class OutputFilter(logging.Filter):
    def __init__(self, is_error, is_audit):
        self.is_error = is_error
        self.is_audit = is_audit

    def filter(self, record):
        # if record.levelno == 25 and self.is_audit:
        #     return True
        if self.is_audit:
            return record.levelno == 25
        else:
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


def audit(message, *args, **kwargs):
    logging.log(25, message, *args, **kwargs)


def setup_logging(config):
    level = logging.DEBUG if config['DEBUG'] else logging.INFO
    # Our logging routines signal the start and end of the routes,
    # so the Werkzeug defaults aren't required. Keep warnings and above.
    logging.getLogger('werkzeug').setLevel(logging.WARN)
    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)
    logging.addLevelName(25, 'AUDIT')

    logging.audit = audit

    global app_name
    app_name = config['APPLICATION_NAME']

    root_logger = logging.getLogger()
    logging.setLogRecordFactory(record_factory)
    formatter = logging.Formatter('%(levelname)s %(asctime)s.%(msecs)03d [%(appname)s] %(file)s #%(line)s %(method)s'
                                  ' %(message)s',
                                  "%Y-%m-%d %H:%M:%S")

    out_handler = logging.StreamHandler(sys.stdout)
    out_handler.addFilter(OutputFilter(False, False))
    out_handler.setFormatter(formatter)
    root_logger.addHandler(out_handler)

    err_handler = logging.StreamHandler(sys.stderr)
    err_handler.addFilter(OutputFilter(True, False))
    err_handler.setFormatter(formatter)
    root_logger.addHandler(err_handler)

    if 'AUDIT_LOG_FILENAME' in config:
        audit_handler = logging.FileHandler(config['AUDIT_LOG_FILENAME'])
    else:
        audit_handler = logging.StreamHandler(sys.stdout)
    audit_handler.addFilter(OutputFilter(False, True))
    audit_handler.setFormatter(formatter)
    root_logger.addHandler(audit_handler)

    root_logger.setLevel(level)
