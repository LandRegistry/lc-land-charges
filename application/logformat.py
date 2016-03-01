from flask import request


def format_message(message):
    if 'X-Transaction-ID' in request.headers:
        return "T:{} {}".format(request.headers['X-Transaction-ID'], message)
    return message
