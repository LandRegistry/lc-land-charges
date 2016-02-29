from flask import session


def format_message(message):
    if 'transaction_id' in session:
        return "T:{} {}".format(session['transaction_id'], message)
    return message
