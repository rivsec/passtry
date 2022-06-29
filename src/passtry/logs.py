import logging


logger = logging.getLogger('passtry')

# NOTE: Disable paramiko's messy output entirely
logging.getLogger('paramiko.transport').addHandler(logging.NullHandler())


def debug(msg):
    logger.debug(msg)


def error(msg):
    logger.error(msg)


def info(msg):
    logger.info(msg)


