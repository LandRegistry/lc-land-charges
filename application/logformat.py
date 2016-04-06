from flask import request


def format_message(message):
    transid = ''
    if 'X-Transaction-ID' in request.headers:
        transid = "T:{}".format(request.headers['X-Transaction-ID'])

    userstr = 'U:?'
    if 'X-LC-Username' in request.headers:
        userstr = "U:{}".format(request.headers['X-LC-Username'])

    return "{} {} {}".format(transid, userstr, message)
