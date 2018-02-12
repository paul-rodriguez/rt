import logging
from abc import ABCMeta, abstractproperty, abstractmethod

from ..hist import (StateScheduleTick,
                    StateArrival,
                    StateCompletion,
                    StateDeadline)

logger = logging.getLogger(__name__)


def convertStateEvent(jobManager, stateEvent):
    convFunc = _conversionFunctions[type(stateEvent)]
    return convFunc(jobManager, stateEvent)


class _Event(metaclass=ABCMeta):

    def __init__(self, time):
        self._time = time

    @property
    def time(self):
        return self._time

    @property
    @abstractmethod
    def priority(self):
        pass

    @abstractmethod
    def execute(self, simulator):
        pass

    @abstractmethod
    def stateConverted(self):
        pass

    def ignore(self):
        return False


class Deadline(_Event):

    def __init__(self, time, job):
        super().__init__(time)
        self._job = job

    @property
    def priority(self):
        return 3, self._job.taskId

    @property
    def job(self):
        return self._job

    def execute(self, simulator):
        simulator.deadline(self._job)

    def stateConverted(self):
        return StateDeadline(self.time, self._job.task, self._job.releaseIndex)

    def __repr__(self):
        return 'Deadline({}, {})'.format(self.time, self._job)


class Arrival(_Event):

    def __init__(self, time, job):
        super().__init__(time)
        self._job = job

    @property
    def priority(self):
        return 2, self._job.taskId

    @property
    def job(self):
        return self._job

    def execute(self, simulator):
        simulator.arrival(self._job)

    def stateConverted(self):
        return StateArrival(self.time, self._job.task, self._job.releaseIndex)

    def __repr__(self):
        return 'Arrival({}, {})'.format(self.time, self._job)


class Completion(_Event):

    def __init__(self, time, job):
        super().__init__(time)
        self._job = job

    @property
    def priority(self):
        return 1, self._job.taskId

    @property
    def job(self):
        return self._job

    def execute(self, simulator):
        simulator.completion(self._job)

    def stateConverted(self):
        return StateCompletion(self.time,
                               self._job.task,
                               self._job.releaseIndex)

    def ignore(self):
        remExec = self._job.remainingExecWithDebt()
        if remExec > 0:
            if self._job.hasBeenStarted():
                completionTime = remExec + self._job.lastStart()
                try:
                    assert completionTime >= self._time
                except AssertionError as e:
                    logger.exception(
                        'Remaining exec time: %s Last start: %s '
                        'Current time: %s',
                        remExec,
                        self._job.lastStart(),
                        self._time)
                    raise e
                ignored = not (self._time == completionTime)
                return ignored
            else:
                return True
        else:
            return False

    def __repr__(self):
        return 'Completion({}, {})'.format(self.time, self._job)


class ScheduleTick(_Event):

    def __init__(self, time):
        super().__init__(time)

    @property
    def priority(self):
        return 4, 0

    def execute(self, simulator):
        simulator.addNextScheduleTicks()

    def stateConverted(self):
        return StateScheduleTick(self.time)

    def __repr__(self):
        return 'ScheduleTick({})'.format(self.time)


def _convertArrival(jobManager, stateArrival):
    job = jobManager.getJob(stateArrival.task, stateArrival.releaseIndex)
    arrival = Arrival(stateArrival.time, job)
    return arrival


def _convertCompletion(jobManager, stateCompletion):
    job = jobManager.getJob(stateCompletion.task, stateCompletion.releaseIndex)
    completion = Completion(stateCompletion.time, job)
    return completion


def _convertDeadline(jobManager, stateDeadline):
    job = jobManager.getJob(stateDeadline.task, stateDeadline.releaseIndex)
    deadline = Deadline(stateDeadline.time, job)
    return deadline


def _convertScheduleTick(jobManager, stateScheduleTick):
    del jobManager
    scheduleTick = ScheduleTick(stateScheduleTick.time)
    return scheduleTick

_conversionFunctions = {StateArrival: _convertArrival,
                        StateCompletion: _convertCompletion,
                        StateDeadline: _convertDeadline,
                        StateScheduleTick: _convertScheduleTick}
