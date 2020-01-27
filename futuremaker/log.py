"""Logging configuration."""
import logging

import os

format = '[%(asctime)s %(levelname)s] (%(filename)s:%(lineno)d) %(message)s'
summary_format = '[%(asctime)s %(levelname)s] [%(filename)s] %(message)s'
formatter = logging.Formatter(format)
summary_formatter = logging.Formatter(format)

logging.basicConfig(format=format, level=os.environ.get('LOGLEVEL', 'INFO'))

# Name the logger after the package.
logger = logging.getLogger(__package__)


def setup_logger(name, log_file, level=logging.INFO, formatter=formatter):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

order_filepath = os.path.join(os.getcwd(), 'order.log')
logger.info('Order log path: %s', order_filepath)
order_logger = setup_logger('order_logger', order_filepath, logging.INFO, summary_formatter)

position_filepath = os.path.join(os.getcwd(), 'position.log')
logger.info('Position log path: %s', position_filepath)
position = setup_logger('position_logger', position_filepath, logging.INFO, summary_formatter)
