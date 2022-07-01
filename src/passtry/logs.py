import logging
import sys


# NOTE: Disable paramiko's messy output entirely
logging.getLogger('paramiko.transport').addHandler(logging.NullHandler())


logger = logging.getLogger('passtry')
formatter = {
    logging.DEBUG: logging.Formatter('%(name)s %(levelname)s [%(asctime)s] %(message)s'),
    logging.INFO: logging.Formatter('[%(asctime)s] %(message)s')
}
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def debug(msg):
    logger.debug(msg)


def error(msg):
    logger.error(msg)


def info(msg):
    logger.info(msg)


def init(loglevel):
    logger.setLevel(loglevel)
    handler.setFormatter(formatter[loglevel])
