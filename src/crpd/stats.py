
import logging
from abc import ABC
from enum import Enum

from .internals.events import Completion
from .utils.eq import ValueEqual

logger = logging.getLogger(__name__)


class _AggregatorStatus(Enum):
    Active = 0
    Inactive = 1


class StatAggregator(ABC):

    @classmethod
    def createInstance(cls, aggregatorTag):
        return aggregatorTag.value()

    def __init__(self):
        super().__init__()
        self.status = _AggregatorStatus.Active

    def aggregate(self,
                  time,
                  jobs,
                  events,
                  scheduler,
                  deadlineMisses,
                  preemptions):
        raise NotImplementedError

    def key(self):
        raise NotImplementedError

    def result(self):
        raise NotImplementedError


class LongestResponseTimeAggregator(StatAggregator):

    def __init__(self):
        super().__init__()
        self._longestResponseTimes = {}

    def aggregate(self,
                  time,
                  jobs,
                  events,
                  scheduler,
                  deadlineMisses,
                  preemptions):
        assert self.status == _AggregatorStatus.Active
        for event in events:
            if isinstance(event, Completion) and not event.ignore():
                task = event.job.task
                releaseTime = event.job.releaseTime
                responseTime = event.time - releaseTime
                try:
                    currentMax = self._longestResponseTimes[task]
                except KeyError:
                    self._longestResponseTimes[task] = 0
                    currentMax = 0
                if responseTime > currentMax:
                    self._longestResponseTimes[task] = responseTime

    def key(self):
        return AggregatorTag.LongestResponseTime

    def result(self):
        self.status = _AggregatorStatus.Inactive
        return self._longestResponseTimes

    def __repr__(self):
        return 'LongestResponseTimeAggregator({})'.format(
            self._longestResponseTimes)


class PreemptionCountAggregator(StatAggregator):

    def __init__(self):
        super().__init__()
        self._nbPreemptions = 0

    def aggregate(self,
                  time,
                  jobs,
                  events,
                  scheduler,
                  deadlineMisses,
                  preemptions):
        assert self.status == _AggregatorStatus.Active
        self._nbPreemptions += len(preemptions)

    def key(self):
        return AggregatorTag.PreemptionCount

    def result(self):
        self.status = _AggregatorStatus.Inactive
        return self._nbPreemptions

    def __repr__(self):
        return 'PreemptionCountAggregator({})'.format(self._nbPreemptions)


class PreemptionTimeAggregator(StatAggregator):

    def __init__(self):
        super().__init__()
        self._preemptionTime = 0

    def aggregate(self,
                  time,
                  jobs,
                  events,
                  scheduler,
                  deadlineMisses,
                  preemptions):
        assert self.status == _AggregatorStatus.Active
        for preemption in preemptions:
            self._preemptionTime += preemption.addedDebt

    def key(self):
        return AggregatorTag.PreemptionTime

    def result(self):
        self.status = _AggregatorStatus.Inactive
        return self._preemptionTime

    def __repr__(self):
        return 'PreemptionTimeAggregator({})'.format(self._preemptionTime)


class ExecutionTimeAggregator(StatAggregator):

    def __init__(self):
        super().__init__()
        self._jobProgress = {}

    def aggregate(self,
                  time,
                  jobs,
                  events,
                  scheduler,
                  deadlineMisses,
                  preemptions):
        del time
        del events
        del scheduler
        del deadlineMisses
        del preemptions
        assert self.status == _AggregatorStatus.Active
        for job in jobs:
            jobId = job.task, job.releaseIndex
            self._jobProgress[jobId] = job.progress()

    def key(self):
        return AggregatorTag.ExecutionTime

    def result(self):
        self.status = _AggregatorStatus.Inactive
        return sum(self._jobProgress.values())

    def __repr__(self):
        return 'ExecutionTimeAggregator({})'.format(
            sum(self._jobProgress.values()))


class AggregatorTag(Enum):
    PreemptionCount = PreemptionCountAggregator
    PreemptionTime = PreemptionTimeAggregator
    ExecutionTime = ExecutionTimeAggregator
    LongestResponseTime = LongestResponseTimeAggregator


class SimulationStatistics(ValueEqual):

    def __init__(self, simulationResult):
        super().__init__()
        self._result = simulationResult

    @property
    def time(self):
        return self._result.time

    def totalExecutionTime(self):
        res = 0
        lastState = self._result.history.lastState()
        lastActiveReleases = {}
        for jobState in lastState.jobs:
            res += jobState.progress
            task = jobState.task
            if task in lastActiveReleases:
                if lastActiveReleases[task] > jobState.releaseIndex:
                    lastActiveReleases[task] = jobState.releaseIndex
            else:
                lastActiveReleases[task] = jobState.releaseIndex
        for task, lastRelease in lastActiveReleases.items():
            res += lastRelease * task.wcet
        return res

    @property
    def totalPreemptionTime(self):
        preemptions = self._result.history.preemptions(timeLimit=self.time)
        total = sum([p.addedDebt for p in preemptions])
        return total

    @property
    def nbOfPreemptions(self):
        preemptions = self._result.history.preemptions(timeLimit=self.time)
        return len(preemptions)
