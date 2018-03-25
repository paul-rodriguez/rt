from abc import ABC
from enum import Enum

from .utils.eq import ValueEqual
from .internals.sched import (EDFScheduler,
                              RMScheduler,
                              DualPriorityScheduler)


class SchedulerTag(Enum):
    EDF = EDFScheduler
    RM = RMScheduler
    DP = DualPriorityScheduler


class AbstractSchedulingPolicy(ABC, ValueEqual):

    def __init__(self):
        super().__init__()

    def createSchedulerInstance(self):
        raise NotImplementedError

    def tag(self):
        raise NotImplementedError


class EDFSchedulingPolicy(AbstractSchedulingPolicy):

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return 'EDFSchedulingPolicy()'

    def createSchedulerInstance(self):
        return EDFScheduler()

    def tag(self):
        return SchedulerTag.EDF


class RMSchedulingPolicy(AbstractSchedulingPolicy):

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return 'RMSchedulingPolicy()'

    def createSchedulerInstance(self):
        return RMScheduler()

    def tag(self):
        return SchedulerTag.RM


class DualPrioritySchedulingPolicy(AbstractSchedulingPolicy):

    def __init__(self, *taskPriorities):
        super().__init__()
        self._taskPriorities = frozenset(taskPriorities)

    def __repr__(self):
        return 'DualPrioritySchedulingPolicy({})'.format(self._taskPriorities)

    def withUpdate(self, *newTaskPriorities):
        prioDict = dict(self._taskPriorities)
        newDict = dict(newTaskPriorities)
        prioDict.update(newDict)
        policy = DualPrioritySchedulingPolicy(*prioDict.items())
        return policy

    def schedulerInfo(self, task):
        for t, info in self._taskPriorities:
            if t is task:
                return info
        raise AssertionError('Task not found in dual priority information.')

    def priorityAt(self, task, relativeTime):
        return self.schedulerInfo(task).priorityAt(relativeTime)

    def lowPriority(self, task):
        return self.schedulerInfo(task).lowPriority()

    def highPriority(self, task):
        return self.schedulerInfo(task).highPriority()

    def hasPromotion(self, task):
        return self.schedulerInfo(task).hasPromotion()

    def promotion(self, task):
        return self.schedulerInfo(task).promotion()

    def createSchedulerInstance(self):
        return DualPriorityScheduler(policy=self)

    def tag(self):
        return SchedulerTag.DP

    def tasks(self):
        return {task for task, _ in self._taskPriorities}

    def promotedTasks(self):
        return {task for task in self.tasks() if self.hasPromotion(task)}

    def items(self):
        return self._taskPriorities


class DualPriorityTaskInfo(ValueEqual):

    def __init__(self, lowPriority, promotion=None, highPriority=None):
        super().__init__()
        self._lowPriority = lowPriority
        self._promotion = promotion
        self._highPriority = highPriority

        if promotion is not None:
            assert highPriority <= lowPriority

    def __repr__(self):
        if self._promotion is None:
            fmt = '{}'.format(self._lowPriority)
        else:
            fmt = '{}, {}, {}'.format(self._lowPriority,
                                      self._promotion,
                                      self._highPriority)

        return 'DualPriorityTaskInfo({})'.format(fmt)

    def hasPromotion(self):
        return self._promotion is not None

    def promotion(self):
        return self._promotion

    def lowPriority(self):
        return self._lowPriority

    def highPriority(self):
        return self._highPriority

    def priorityAt(self, relativeTime):
        if not self.hasPromotion() or (relativeTime < self._promotion):
            return self._lowPriority
        else:
            return self._highPriority
