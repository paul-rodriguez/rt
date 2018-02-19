import logging

from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationSetup, SimulationRun
from crpd.stats import AggregatorTag
from .internals import (baseRMPolicy,
                        getHistory,
                        rmSortedTasks)

logger = logging.getLogger(__name__)


class OptimisationFailure(Exception):
    pass


class AbstractThreeTaskOptimiser:

    def __init__(self, taskset):
        super().__init__()
        self._taskset = taskset
        self._optimised = None
        self._history = None

    @property
    def taskset(self):
        return self._taskset

    def optimisedPolicy(self):
        if self._optimised is None:
            self._optimised = self._buildOptimised()
        return self._optimised

    def history(self):
        if self._history is None:
            self._history = getHistory(self.taskset, self.optimisedPolicy())
        return self._history

    def success(self):
        return not self.history().hasDeadlineMiss()

    def _buildOptimised(self):
        raise NotImplementedError

    def _buildWithPromo2(self, promo2):
        t1, t2, t3 = tuple(rmSortedTasks(self.taskset))

        promo1 = t1.minimalInterArrivalTime - t1.wcet
        schedulerInfo1 = DualPriorityTaskInfo(3, promo1, -3)
        schedulerInfo2 = DualPriorityTaskInfo(2, promo2, -2)
        schedulerInfo3 = DualPriorityTaskInfo(1)
        policy = DualPrioritySchedulingPolicy((t1, schedulerInfo1),
                                              (t2, schedulerInfo2),
                                              (t3, schedulerInfo3))
        return policy


class FixedPointThreeTaskOptimiser(AbstractThreeTaskOptimiser):

    def __init__(self, taskset):
        super().__init__(taskset)

    def _buildOptimised(self):
        task1, task2, _ = tuple(rmSortedTasks(self.taskset))
        hyperperiod = self.taskset.hyperperiod

        t1 = task1.minimalInterArrivalTime
        c1 = task1.wcet
        t2 = task2.minimalInterArrivalTime
        c2 = task2.wcet

        promo2 = _fixedPointPromoT2(hyperperiod, c1, t1, c2, t2)
        policy = self._buildWithPromo2(promo2)
        return policy


class RMWorstCaseLaxity3TaskOptimiser(AbstractThreeTaskOptimiser):

    def __init__(self, taskset):
        super().__init__(taskset)

    def _buildOptimised(self):
        _, t2, _ = tuple(rmSortedTasks(self.taskset))
        rmPolicy = baseRMPolicy(self.taskset)
        hyperperiod = self.taskset.hyperperiod
        aggregators = (AggregatorTag.LongestResponseTime,)
        setup = SimulationSetup(self.taskset,
                                time=hyperperiod,
                                schedulingPolicy=rmPolicy,
                                aggregatorTags=aggregators)
        result = SimulationRun(setup).result()
        longestResponseTimes = result.aggregateStat(
            AggregatorTag.LongestResponseTime)
        t2RT = longestResponseTimes[t2]
        period2 = t2.minimalInterArrivalTime

        policy = self._buildWithPromo2(period2 - t2RT)
        return policy


def _interferenceInInterval(start,
                            end,
                            iOffset,
                            iPeriod,
                            iLength):
    firstInterferenceIndex = 1 + (start - 1 - (iLength + iOffset)) // iPeriod
    firstInterferenceStart = iOffset + firstInterferenceIndex * iPeriod

    firstPartial = max(0, start - firstInterferenceStart)

    lastInterferenceIndex = (end - iOffset) // iPeriod
    lastInterferenceStart = iOffset + lastInterferenceIndex * iPeriod
    lastInterferenceEnd = lastInterferenceStart + iLength

    lastPartial = max(0, lastInterferenceEnd - end)

    interferenceSum = (
        iLength * max(0, 1 + lastInterferenceIndex - firstInterferenceIndex))
    interferenceTotal = interferenceSum - (firstPartial + lastPartial)
    return interferenceTotal


def _firstJobPromoT2(c1, t1, c2, t2):
    s1 = t1 - c1

    oldPromo2 = t2
    promo2 = t2 - c2
    while promo2 != oldPromo2:
        oldPromo2 = promo2
        interference = _interferenceInInterval(promo2,
                                               t2,
                                               s1,
                                               t1,
                                               c1)
        if promo2 > t2 - c2 - interference:
            promo2 = t2 - c2 - interference
            if promo2 < 0:
                raise OptimisationFailure
            break
    return promo2


def _fixedPointPromoT2(hyperperiod, c1, t1, c2, t2):
    s1 = t1 - c1
    oldPromo2 = t2
    promo2 = t2 - c2
    while promo2 != oldPromo2:
        oldPromo2 = promo2
        for q in range(1, int(hyperperiod // t2)):
            t2PromotionTime = t2 * (q - 1) + promo2
            t2DeadlineTime = t2 * q

            totalInterference = _interferenceInInterval(t2PromotionTime,
                                                        t2DeadlineTime,
                                                        s1,
                                                        t1,
                                                        c1)

            if promo2 > t2 - c2 - totalInterference:
                promo2 = t2 - c2 - totalInterference
                if promo2 < 0:
                    raise OptimisationFailure
                break
    return promo2
