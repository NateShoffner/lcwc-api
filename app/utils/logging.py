import logging
from logging.handlers import TimedRotatingFileHandler

def get_custom_logger(name: str):

    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(message)s')

    # console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_logger = TimedRotatingFileHandler('./logs/logfile.log', when='midnight', backupCount=10, delay=True)
    file_logger.setFormatter(formatter)
    file_logger.setLevel(logging.INFO)
    logger.addHandler(file_logger)

    file_error_logger = TimedRotatingFileHandler('./logs/logfile-error.log', when='midnight', backupCount=10, delay=True)
    file_error_logger.setFormatter(formatter)
    file_error_logger.setLevel(logging.ERROR)
    logger.addHandler(file_error_logger)

    return logger