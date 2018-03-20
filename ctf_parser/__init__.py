import logging
from logging.handlers import TimedRotatingFileHandler

logger = logging.getLogger('CtF Parser')
logger.setLevel(logging.DEBUG)

fh = TimedRotatingFileHandler('parser.log', when='midnight')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)
