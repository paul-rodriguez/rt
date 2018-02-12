
import logging


class SimulationError(Exception):

    logHandler = logging.FileHandler('/tmp/simulationErrors.log')
    logger = logging.getLogger('simulationErrors')
    logger.addHandler(logHandler)

    def __init__(self, message, setup, history):
        self.message = message
        self.setup = setup
        self.history = history

    def __repr__(self):
        msg = ('SimulationError raised: {} \n'
               'Setup: {} \n'
               'History: {}'.format(self.message, self.setup, self.history))
        return msg

    def saveToFile(self):
        SimulationError.logger.error('%s', self)
