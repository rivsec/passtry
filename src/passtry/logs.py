import logging


logger = logging.getLogger('passtry')


def debug(msg):
    logger.debug(msg)


def error(msg):
    logger.error(msg)


def info(msg):
    logger.info(msg)


