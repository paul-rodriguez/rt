
import logging
import queue
from time import sleep
from multiprocessing import Process, Queue, Semaphore
from enum import Enum
from abc import ABC

from .sim import SimulationRun
from .utils.persistence import FileEnv
from .utils.eq import ValueEqual

logger = logging.getLogger(__name__)


class RunnerStatus(Enum):
    CREATED = 0
    STARTED = 1
    ENDED = 2


class InterruptibleRunner:

    def __init__(self, setupPath, resultPath):

        self._setupFiles = FileEnv(rootPath=setupPath, manifest=True)
        self._resultFiles = FileEnv(rootPath=resultPath, manifest=False)
        self._setups = {setup: key for key, setup in self._setupFiles.items()}
        self._resultsManifest = _ResultsManifest(resultPath + '/manifest.txt')
        self._resultDict = dict(self._loadManifest())

        logger.info('Total existing results: {}'.format(
            len(self._resultDict)))

    def nbResults(self):
        return len(self._resultDict)

    def setups(self):
        return self._setups.keys()

    def getResult(self, setup):
        fileKey = self._resultDict[setup]
        result = self._resultFiles.load(fileKey)
        return result

    def loadResults(self):
        for fileKey in self._resultsManifest.results():
            yield self._resultFiles.load(fileKey)

    def _loadManifest(self):
        for fileKey in self._resultsManifest.results():
            result = self._resultFiles.load(fileKey)
            setup = result.setup
            logger.debug('Existing result {} for {}'.format(fileKey, setup))
            yield setup, fileKey

    def saveSetups(self, setups):
        for setup in setups:
            setupKey = 'setup#{:0>8}'.format(len(self._setups))
            self._setupFiles.save(setup, setupKey)
            self._setups[setup] = setupKey

    def run(self, nbProcesses):
        remSetups = set()

        for s in self.setups():
            if s not in self._resultDict.keys():
                remSetups.add(s)

        runner = simulationRunner(remSetups,
                                  nbProcesses=nbProcesses,
                                  saveToFile=self._resultFiles)
        runner.start()
        unsyncResults = 0
        while remSetups:
            availResults = runner.availableResults(delete=True)
            for setup, resultKey in availResults.items():
                logger.info('Adding file: {}'.format(resultKey))
                self._resultDict[setup] = resultKey
                self._resultsManifest.add(resultKey)
                unsyncResults += 1
                if unsyncResults > 100:
                    self._resultsManifest.save()
                    unsyncResults = 0
            remSetups -= availResults.keys()
            if not availResults:
                if unsyncResults > 0:
                    self._resultsManifest.save()
                    unsyncResults = 0
                else:
                    sleep(0.5)
        if unsyncResults > 0:
            self._resultsManifest.save()
        runner.join()


def simulationRunner(setups,
                     errorHandling=True,
                     multicore=True,
                     nbProcesses=4,
                     saveToFile=None):
    if multicore:
        return _MulticoreSimulationRunner(setups,
                                          errorHandling,
                                          saveToFile=saveToFile,
                                          nbProcesses=nbProcesses)
    else:
        return _MonocoreSimulationRunner(setups,
                                         errorHandling=errorHandling,
                                         saveToFile=saveToFile)


class _ResultsManifest:

    def __init__(self, filePath, loadFile=True):
        super().__init__()
        self._filePath = filePath
        self._results = set()
        if loadFile:
            self.load()

    def results(self):
        return self._results

    def add(self, fileKey):
        self._results.add(fileKey)

    def save(self):
        with open(self._filePath, 'w') as file:
            for result in self._results:
                file.write('{}\n'.format(result))

    def load(self):
        try:
            with open(self._filePath) as file:
                for line in file.readlines():
                    result = line.rstrip()
                    self._results.add(result)
        except FileNotFoundError:
            pass


def _saveResult(index, result, fileEnv):
    baseKey = 'simuResult#{:0>6}'.format(index)
    key = fileEnv.save(result, baseKey, timedKey=True)
    return key


class _AbstractSimulationRunner(ABC):

    def __init__(self, setups, errorHandling=True, saveToFile=None):
        self._setups = list(setups)
        self._remResults = len(self._setups)
        self._status = RunnerStatus.CREATED
        self._results = {}
        self._errorHandling = errorHandling
        if saveToFile is not None:
            self._fileEnv = saveToFile
            self._saveToFile = True
        else:
            self._saveToFile = False

    @property
    def setups(self):
        return self._setups

    def start(self):
        assert self._status == RunnerStatus.CREATED
        self._status = RunnerStatus.STARTED
        logger.debug('Beginning')
        self._startSimulations()

    def gotAllResults(self):
        return self._remResults == 0

    def join(self):
        self._joinResults()
        self._status = RunnerStatus.ENDED

    def availableResults(self, delete=False):
        self._updateResults()
        retval = self._results
        if delete:
            self._results = {}
        return retval

    def result(self, setup, delete=False):
        """
        Returns the result for @p setup if available, `None` otherwise.

        If @p delete is True, the result is removed from this structure.
        """
        self._updateResults()
        result = self._results.get(setup)
        logger.debug('got result')
        logger.debug(result)
        if delete and result is not None:
            self._results[setup] = None
        return result

    def _updateResults(self):
        raise NotImplementedError

    def _joinResults(self):
        raise NotImplementedError

    def _startSimulations(self):
        raise NotImplementedError


class _MonocoreSimulationRunner(_AbstractSimulationRunner):

    def __init__(self, setups, errorHandling, saveToFile=None):
        super().__init__(setups, errorHandling, saveToFile)

    def _setResult(self, index, result):
        setup = result.setup
        if self._saveToFile:
            key = _saveResult(index, result, self._fileEnv)
            self._results[setup] = key
        else:
            self._results[setup] = result

    def _startSimulations(self):
        for i, setup in enumerate(self._setups):
            run = SimulationRun(setup, errorHandling=self._errorHandling)
            result = run.result()
            self._setResult(i, result)
            self._remResults -= 1

    def _updateResults(self):
        pass

    def _joinResults(self):
        pass


class _MulticoreSimulationRunner(_AbstractSimulationRunner):

    def __init__(self, setups, errorHandling, nbProcesses, saveToFile=None):
        super().__init__(setups, errorHandling, saveToFile)
        self._nbProcesses = nbProcesses
        self._setupQueue = Queue()
        for i, setup in enumerate(self._setups):
            self._setupQueue.put((i, setup))
        self._workSemaphore = Semaphore(self._remResults)
        self._resultQueue = Queue(100)
        self._processes = []

    def _startSimulations(self):
        for processIdx in range(self._nbProcesses):
            target = self._createTarget()
            name = 'SimulationRunner worker #{}'.format(processIdx)
            processArgs = (self._setupQueue,
                           self._resultQueue,
                           self._workSemaphore)
            process = Process(target=target,
                              name=name,
                              args=processArgs)
            process.daemon = True
            self._processes.append(process)
        for process in self._processes:
            process.start()

    def _createTarget(self):
        if self._saveToFile:
            return _ProcessTarget(self._errorHandling,
                                  self._saveToFile,
                                  fileEnv=self._fileEnv)
        else:
            return _ProcessTarget(self._errorHandling, self._saveToFile)

    def _updateResults(self):
        gotResults = False
        while self._remResults > 0:
            try:
                setup, result = self._resultQueue.get_nowait()
            except queue.Empty:
                break
            else:
                logger.debug('Added result for %s', setup)
                logger.debug('Queue depth %d', self._resultQueue.qsize())
                self._results[setup] = result
                self._remResults -= 1
                gotResults = True
        if gotResults:
            logger.debug('Results updated, %d remaining', self._remResults)

    def _joinResults(self):
        logger.debug('Joining results')
        while self._remResults > 0:
            setup, result = self._resultQueue.get()
            logger.debug('Added result for %s', setup)
            self._results[setup] = result
            self._remResults -= 1
        assert self._resultQueue.empty()
        logger.debug('Results joined')
        for process in self._processes:
            process.join()


class _ProcessTarget:

    def __init__(self, errorHandling, saveToFile, fileEnv=None):
        super().__init__()
        self._errorHandling = errorHandling
        self._saveToFile = saveToFile
        if saveToFile:
            assert fileEnv is not None
            self._fileEnv = fileEnv

    def __call__(self, setupQueue, resultQueue, workSemaphore):
        while True:
            availableWork = workSemaphore.acquire(timeout=0)
            if availableWork:
                index, setup = setupQueue.get()
                run = SimulationRun(setup, errorHandling=self._errorHandling)
                result = run.result()
                if self._saveToFile:
                    key = _saveResult(index, result, self._fileEnv)
                    resultQueue.put((setup, key))
                else:
                    resultQueue.put((setup, result))
                del result
            else:
                break
        logger.debug('End of worker process')
