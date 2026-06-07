# log wrapper to enable logging to plugin specific logfile

import os
import logging
from logging.handlers import RotatingFileHandler
import stashapi.log


TRACE = logging.TRACE
DEBUG = logging.DEBUG
INFO  = logging.INFO
WARN  = logging.WARN
ERROR = logging.ERROR

__logger = None

def setup_file(file_name: str, log_level):
    global __logger
    
    file_path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)

    __logger = logging.getLogger(file_name)
    __logger.setLevel(log_level)
    logger_handler = RotatingFileHandler(file_path, maxBytes=2*1024*1024, backupCount=2)
    logger_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    __logger.addHandler(logger_handler)

def error(*args, **kwargs):
    global __logger
    
    stashapi.log.error(*args, **kwargs)
    
    if __logger is not None:
        __logger.error(*args, **kwargs)

def warn(*args, **kwargs):
    global __logger
    
    stashapi.log.warn(*args, **kwargs)
    
    if __logger is not None:
        __logger.warn(*args, **kwargs)

def info(*args, **kwargs):
    global __logger
    
    stashapi.log.info(*args, **kwargs)
    
    if __logger is not None:
        __logger.info(*args, **kwargs)

def debug(*args, **kwargs):
    global __logger
    
    stashapi.log.debug(*args, **kwargs)
    
    if __logger is not None:
        __logger.debug(*args, **kwargs)

def trace(*args, **kwargs):
    global __logger
    
    stashapi.log.trace(*args, **kwargs)
    
    if __logger is not None:
        __logger.trace(*args, **kwargs)
