import logging


def displayModuleLogs(moduleName):
    logger = logging.getLogger(moduleName)
    logger.setLevel(logging.DEBUG)
