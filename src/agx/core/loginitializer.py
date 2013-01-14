import logging
import sys


loghandler = None


def initLog(filename):
    """Initialise the logger.

    This needs only to be called from main and tests/runalltests.py.
    """
    log = logging.getLogger()
    hdlr = logging.FileHandler(filename, 'w')
    formatter = logging.Formatter('%(name)-10s %(levelname)-5s %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)


def addConsoleLogging():
    """Add logging to the console.

    This needs only to be called from main.
    """
    log = logging.getLogger()
    hdlr = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)-5s %(message)s')
    hdlr.setLevel(logging.INFO)
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    return hdlr


def opt_callback(option, opt, value, parser):
    log = logging.getLogger('loginitializer')
    loghandler.setLevel(logging.DEBUG)
