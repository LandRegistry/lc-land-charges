import kombu
from kombu.common import maybe_declare
import sys
import logging


def setup_messaging(config):
    host = "amqp://{}:{}@{}:{}".format(config['MQ_USERNAME'], config['MQ_PASSWORD'], config['MQ_HOSTNAME'],
                                       config['MQ_PORT'])
    logging.debug("Connect to " + host)
    connection = kombu.Connection(hostname=host)
    channel = connection.channel()
    exchange = kombu.Exchange(type="topic", name="new.bankruptcy")
    exchange.maybe_bind(channel)
    maybe_declare(exchange, channel)
    prod = kombu.Producer(channel, exchange=exchange, routing_key='simple', serializer='json')
    logging.info("Producer started")
    sys.stdout.flush()
    return prod


def publish_new_bankruptcy(producer, data):
    publish = {
        "application": "new",
        "data": data
    }
    logging.info("Sending: %s", publish)
    producer.publish(publish)


def publish_amendment(producer, data):
    publish = {
        "application": "amend",
        "data": data
    }
    logging.info("Sending: %s", publish)
    producer.publish(publish)


def publish_cancellation(producer, data):
    publish = {
        "application": "cancel",
        "data": data
    }
    logging.info("Sending: %s", publish)
    producer.publish(publish)