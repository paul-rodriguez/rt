
import logging
import math
from numpy.random import RandomState

from .utils.eq import ValueEqual
from .utils.math import lcm

logger = logging.getLogger(__name__)


class Taskset(ValueEqual):

    def __init__(self, *tasks):
        super().__init__()
        self._tasks = tasks

    def __iter__(self):
        return iter(self._tasks)

    def __repr__(self):
        tasksStr = ', '.join([str(t) for t in self._tasks])
        return 'Taskset({})'.format(tasksStr)

    def __len__(self):
        return len(self._tasks)

    @property
    def hyperperiod(self):
        res = 1
        for task in self._tasks:
            res = lcm(res, task.arrivalDistribution.minimal)
        return res

    @property
    def utilization(self):
        return sum(t.utilization for t in self)

    @property
    def maxPeriod(self):
        return max(task.minimalInterArrivalTime for task in self._tasks)

    def laxEquality(self, other):
        otherTasks = set(other)
        for t1 in self:
            foundTask = None
            for t2 in otherTasks:
                if t1.laxEquality(t2):
                    foundTask = t2
                    break
            if foundTask is None:
                return False
            otherTasks.remove(foundTask)
        return not otherTasks


class Task(ValueEqual):

    _uniqueIdCounter = 0

    def __init__(self,
                 wcet,
                 deadline,
                 arrivalDistrib=None,
                 preemptionCost=None,
                 displayName=None,
                 uniqueId=None):
        super().__init__()
        assert wcet > 0
        self._wcet = wcet
        self._deadline = deadline
        self._displayName = displayName

        if arrivalDistrib is None:
            arrivalDistrib = FixedArrivalDistribution(self._deadline)
        self._arrivalDistrib = arrivalDistrib

        if preemptionCost is None:
            preemptionCost = FixedPreemptionCost(0)
        self._preemptionCost = preemptionCost

        if uniqueId is None:
            uniqueId = Task._uniqueIdCounter
            Task._uniqueIdCounter += 1
        self._uniqueId = uniqueId

    def laxEquality(self, other):
        if self == other:
            return True
        else:
            selfVal = (self.wcet,
                       self.deadline,
                       self.arrivalDistribution,
                       self.preemptionCost)
            otherVal = (other.wcet,
                        other.deadline,
                        other.arrivalDistribution,
                        other.preemptionCost)
            return selfVal == otherVal

    @property
    def utilization(self):
        return self.wcet / self.minimalInterArrivalTime

    @property
    def uniqueId(self):
        return self._uniqueId

    @property
    def wcet(self):
        return self._wcet

    @property
    def deadline(self):
        return self._deadline

    @property
    def minimalInterArrivalTime(self):
        return self._arrivalDistrib.minimal

    @property
    def arrivalDistribution(self):
        return self._arrivalDistrib

    @property
    def preemptionCost(self):
        return self._preemptionCost

    def arrivalTime(self, releaseIndex):
        return self._arrivalDistrib.arrivalTime(releaseIndex)

    def _nonValueFields(self):
        return '_displayName',

    def __repr__(self):
        if self._displayName is not None:
            return self._displayName
        else:
            fmtStr = 'Task({}, {}, {}, {})'
            items = (self.wcet,
                     self.deadline,
                     self._arrivalDistrib,
                     self._preemptionCost)
            return fmtStr.format(*items)

    def __lt__(self, other):
        raise NotImplementedError

    def __le__(self, other):
        raise NotImplementedError

    def __gt__(self, other):
        raise NotImplementedError

    def __ge__(self, other):
        raise NotImplementedError


class FixedPreemptionCost(ValueEqual):

    def __init__(self, cost):
        super().__init__()
        self._cost = cost

    def cost(self, job):
        del job
        return self._cost

    def __repr__(self):
        return 'FixedPC({})'.format(self._cost)


class LogPreemptionCost(ValueEqual):

    def __init__(self, fixedCost, timeRatio):
        super().__init__()
        self._fixedCost = fixedCost
        self._timeRatio = timeRatio

    def cost(self, job):
        baseArea = self._baseArea(job)
        remWcet = job.remainingWcet()
        progress = job.progress()
        remArea = self._logArea(remWcet)
        progressArea = self._logArea(progress)
        totalArea = baseArea - remArea - progressArea
        areaCost = int(math.floor(totalArea * self._timeRatio))
        finalDebt = self._fixedCost + areaCost
        logger.debug('Calculating debt with base area %f from exec time %s',
                     baseArea,
                     job.wcet)
        logger.debug('Remaining area %f from exec time %s', remArea, remWcet)
        logger.debug('Progress area %f from exec time %s',
                     progressArea,
                     progress)
        logger.debug('Debt is %s (floor of %s plus total area %f times %s)',
                     finalDebt,
                     self._fixedCost,
                     totalArea,
                     self._timeRatio)
        return finalDebt

    def _baseArea(self, job):
        wcet = job.wcet
        return self._logArea(wcet)

    @staticmethod
    def _logArea(execTime):
        if execTime == 0:
            return 0
        rectangleArea = execTime * math.log(execTime)
        shadeArea = (execTime - 1)
        area = rectangleArea - shadeArea
        return area

    def __repr__(self):
        return 'LogPC({}, {})'.format(self._fixedCost, self._timeRatio)


class FixedArrivalDistribution(ValueEqual):

    def __init__(self, period):
        super().__init__()
        self._period = period

    @property
    def minimal(self):
        return self._period

    def arrivalTime(self, releaseIndex):
        return self._period * releaseIndex

    def __repr__(self):
        return "FixedAD({})".format(self._period)


class PoissonArrivalDistribution(ValueEqual):

    def __init__(self, minimal, lambdaFactor, seed=None):
        super().__init__()
        self._minimal = minimal
        self._lambda = lambdaFactor

        if seed is None:
            seed = 0
        self._seed = seed

        self._random = RandomState(seed)
        self._arrivalMap = {}

    def _nonValueFields(self):
        return '_random', '_arrivalMap'

    @property
    def minimal(self):
        return self._minimal

    @property
    def lambdaFactor(self):
        return self._lambda

    def arrivalTime(self, releaseIndex):
        if releaseIndex == 0:
            return 0
        if releaseIndex not in self._arrivalMap:
            previous = self.arrivalTime(releaseIndex - 1)
            sample = self._random.poisson(self._lambda) + self._minimal
            arrival = sample + previous
            self._arrivalMap[releaseIndex] = arrival
        else:
            arrival = self._arrivalMap[releaseIndex]
        return arrival

    def __repr__(self):
        return "PoissonAD({}, {}, {})".format(self._minimal,
                                              self._lambda,
                                              self._seed)
