import logging
from collections import namedtuple
from abc import ABC, abstractmethod
from heapq import heappush, heapreplace, heappop, heapify

from ..hist import (EDFSchedulerState,
                    RMSchedulerState,
                    DualPrioritySchedulerState)

logger = logging.getLogger(__name__)

"""
This namedtuple represents a transition from one running job to another.

This can contain instances of _Job and None.
Naturally, a transition from None to a job means that the processor was idle
and is becoming active, while a transition from a job to None means that the
processor becomes idle.
"""
ScheduleTransition = namedtuple('ScheduleTransition', ['old', 'new'])


class SchedulerFactory:

    @staticmethod
    def fromPolicy(schedulingPolicy):
        scheduler = schedulingPolicy.createSchedulerInstance()
        return scheduler

    @staticmethod
    def fromState(schedulerState, jobManager):
        convFunc = SchedulerFactory._conversionFunctions[type(schedulerState)]
        return convFunc(jobManager, schedulerState)

    @staticmethod
    def _convertEDF(jobManager, edfState):
        return EDFScheduler(jobManager, edfState)

    @staticmethod
    def _convertRM(jobManager, rmState):
        return RMScheduler(jobManager, rmState)

    @staticmethod
    def _convertDP(jobManager, dpState):
        return DualPriorityScheduler(jobManager=jobManager,
                                     schedulerState=dpState)

    _conversionFunctions = {
        EDFSchedulerState: (
            lambda *x: SchedulerFactory._convertEDF(*x)),
        RMSchedulerState: (
            lambda *x: SchedulerFactory._convertRM(*x)),
        DualPrioritySchedulerState: (
            lambda *x: SchedulerFactory._convertDP(*x))
    }


class AbstractScheduler(ABC):
    """
    Extend this class to implement a new scheduler where job priorities can
    change during job lifetime.
    Otherwise, extend QueueBasedScheduler.

    This class declares the scheduler API through abstract methods and
    provides very basic support for the currently running job.
    """

    def __init__(self):
        super().__init__()
        self._runningEntry = None

    def nextScheduleTicks(self, time):
        """
        Returns a collection of times strictly greater than @p time at which
        the schedule must be re-computed independently of other events.

        :param time:
        :return:
        """
        return []

    @abstractmethod
    def schedulerState(self):
        """
        A snapshot of the current state of the scheduler.

        Each subclass must redefine this function to return some instance of
        SchedulerState (or a subclass) such that the original scheduler may be
        built back from that instance using self._initFromState().

        :return:    A SchedulerState subclass instance.
        """
        raise NotImplementedError

    @abstractmethod
    def _initFromState(self, schedulerState, jobManager):
        """
        Subclasses must call this method to initialise the basic scheduler
        structures when constructing from a scheduler state.

        :param schedulerState:
        :param jobManager:
        """

        if schedulerState.runningEntry is None:
            self._runningEntry = None
        else:
            topPrio, topTask, topIndex = schedulerState.basicRunningEntry()
            runningJob = jobManager.getJob(topTask, topIndex)
            self._runningEntry = topPrio, runningJob

    @abstractmethod
    def addReadyJob(self, job):
        """
        Signal to the scheduler that a new job is ready.

        :param job:
        """
        raise NotImplementedError

    @abstractmethod
    def schedule(self, time):
        """
        Determine which job should currently be running.

        Subclasses must update self._runningEntry according to their policy.

        :param      time:
                    The current time of the simulator.
        :return:    A SchedulerTransition value that corresponds to the
                    action taken.
        """
        raise NotImplementedError

    def _onExecutionCompleted(self, priority, job):
        """
        Triggered when the simulator signals the scheduler that a job has
        completed its execution.

        Subclasses can redefine this function if needed.

        :param priority:    The priority of the completed job.
        :param job:         The completed job.
        :return: Nothing.
        """
        pass

    def initializeSchedulerData(self, taskset):
        """
        Subclasses can redefine this function if they need access to taskset
        information before the simulation begins.

        :param taskset:
        :return: Nothing.
        """
        pass

    def runningJob(self):
        if self._runningEntry is not None:
            _, job = self._runningEntry
            return job
        else:
            return None

    def executionCompleted(self):
        priority, job = self._runningEntry
        self._onExecutionCompleted(priority, job)
        self._runningEntry = None


class QueueBasedScheduler(AbstractScheduler):
    """
    Extend this class when creating a scheduler where priorities do not change
    during a job's lifetime.
    """

    def __init__(self):
        """
        Subclasses must call QueueBasedScheduler._initFromState() at the end of
        their constructor when building from a scheduler state structure.
        """

        super().__init__()
        self._readyQueue = []

    @abstractmethod
    def _initFromState(self, schedulerState, jobManager):
        """
        Subclasses must call this method to initialise the queue-based
        scheduler structures when constructing from a scheduler state.

        :param schedulerState:
        :param jobManager:
        """
        super()._initFromState(schedulerState, jobManager)

        def genEntries():
            for (prio, task, index) in schedulerState.basicReadyEntries():
                readyJob = jobManager.getJob(task, index)
                yield prio, readyJob

        self._readyQueue = list(genEntries())
        heapify(self._readyQueue)

    @abstractmethod
    def _computePriority(self, job):
        """
        The current priority of @p job

        :param job:     A job (running or ready).
        :return:        The priority of @p job.
        """
        raise NotImplementedError

    def addReadyJob(self, job):
        logger.debug('Adding ready %s', job)
        priority = self._computePriority(job)
        entry = (priority, job)
        assert entry not in self._readyQueue
        heappush(self._readyQueue, entry)

    def schedule(self, time):
        del time
        result = ScheduleTransition(None, None)
        if self._readyQueue:
            priority, readyJob = self._readyQueue[0]
            if self._runningEntry is None:
                self._runningEntry = priority, readyJob
                heappop(self._readyQueue)
                logger.debug(
                    'Scheduling from idle at priority %s : %s',
                    priority,
                    readyJob)
                result = ScheduleTransition(None, readyJob)
            else:
                runningPriority, runningJob = self._runningEntry
                if priority < runningPriority:
                    logger.debug(
                        'Preempting %s priority %s with %s priority %s',
                        runningJob, runningPriority, readyJob, priority)
                    heapreplace(self._readyQueue, self._runningEntry)
                    _, runningJob = self._runningEntry
                    self._runningEntry = priority, readyJob
                    result = ScheduleTransition(runningJob, readyJob)
                else:
                    logger.debug('No schedule change: %s', runningJob)

                    result = ScheduleTransition(runningJob, runningJob)
        elif self._runningEntry is not None:
            runningPriority, runningJob = self._runningEntry
            logger.debug('No schedule change: %s', runningJob)
            result = ScheduleTransition(runningJob, runningJob)
        else:
            logger.debug('Nothing to schedule')
        logger.debug('Schedule done')
        logger.debug('Ready queue: %s', self._readyQueue)
        return result


class EDFScheduler(QueueBasedScheduler):

    def __init__(self, jobManager=None, schedulerState=None):
        super().__init__()
        self._collisionDicts = {}

        if schedulerState is not None:
            self._initFromState(schedulerState, jobManager)

    def _initFromState(self, schedulerState, jobManager):
        super()._initFromState(schedulerState, jobManager)
        for priority, job in self._readyQueue:
            self._addToCollisions(job, priority)
        if self._runningEntry is not None:
            topPrio, runningJob = self._runningEntry
            self._addToCollisions(runningJob, topPrio)

    def schedulerState(self):
        entries = [self._stateEntry(prio, j)
                   for prio, j in self._readyQueue]
        if self._runningEntry is None:
            runningEntry = None
        else:
            priority, job = self._runningEntry
            runningEntry = self._stateEntry(priority, job)
        return EDFSchedulerState(runningEntry, *entries)

    @staticmethod
    def _stateEntry(priority, job):
        deadline, collision = priority
        task = job.task
        releaseIndex = job.releaseIndex
        return deadline, collision, task, releaseIndex

    def _onExecutionCompleted(self, priority, job):
        deadline, _ = priority
        collisionDict = self._collisionDicts[deadline]
        del collisionDict[job]
        if not collisionDict:
            del self._collisionDicts[deadline]

    def _computePriority(self, job):
        deadline = job.deadline
        try:
            collisionDict = self._collisionDicts[deadline]
        except KeyError:
            self._collisionDicts[deadline] = {job: 0}
            index = 0
        else:
            try:
                index = collisionDict[job]
            except KeyError:
                index = max(collisionDict.values()) + 1
                collisionDict[job] = index
        return deadline, index

    def _addToCollisions(self, job, priority):
        deadline, index = priority
        try:
            collisionDict = self._collisionDicts[deadline]
        except KeyError:
            collisionDict = {}
            self._collisionDicts[deadline] = collisionDict
        collisionDict[job] = index

    def __repr__(self):
        readyStr = ', '.join([str(e) for e in self._readyQueue])
        return 'EDFScheduler({}, ready[{}])'.format(self._runningEntry,
                                                    readyStr)


class RMScheduler(QueueBasedScheduler):

    def __init__(self, jobManager=None, schedulerState=None):
        super().__init__()

        if schedulerState is not None:
            self._initFromState(schedulerState, jobManager)

    def schedulerState(self):
        entries = [(j.task, j.releaseIndex) for _, j in self._readyQueue]
        if self._runningEntry is None:
            runningEntry = None
        else:
            _, job = self._runningEntry
            runningEntry = (job.task, job.releaseIndex)
        return RMSchedulerState(runningEntry, *entries)

    def _initFromState(self, schedulerState, jobManager):
        super()._initFromState(schedulerState, jobManager)

    def _computePriority(self, job):
        task = job.task
        return task.minimalInterArrivalTime, task.uniqueId, job.releaseIndex

    def __repr__(self):
        readyStr = ', '.join([str(e) for e in self._readyQueue])
        return 'RMScheduler({}, ready[{}])'.format(self._runningEntry,
                                                   readyStr)


class DualPriorityScheduler(AbstractScheduler):

    def __init__(self, policy=None, jobManager=None, schedulerState=None):
        super().__init__()

        self._promotedTasks = None
        self._promotionsHeap = None

        self._readyJobs = set()
        if schedulerState is not None:
            self._initFromState(schedulerState, jobManager)
        else:
            assert policy is not None
            self._policy = policy

    def initializeSchedulerData(self, taskset):
        def promoTasks():
            priorityValues = []
            for task in taskset:
                priorityValues.append(self._policy.lowPriority(task))
                if self._policy.hasPromotion(task):
                    priorityValues.append(self._policy.highPriority(task))
                    yield task
            # Assert that there are no duplicate priority values
            assert len(priorityValues) == len(set(priorityValues))

        self._promotedTasks = list(promoTasks())
        self._promotionsHeap = [(self._policy.promotion(t), 0, i, t)
                                for i, t in enumerate(self._promotedTasks)]
        heapify(self._promotionsHeap)

    def _topPromo(self):
        promo, _, _, _ = self._promotionsHeap[0]
        return promo

    def _nextPromo(self):
        promo, release, index, task = self._promotionsHeap[0]
        heappop(self._promotionsHeap)
        newPromo = self._policy.promotion(task) + task.arrivalTime(release)
        entry = newPromo, release + 1, index, task
        heappush(self._promotionsHeap, entry)
        return self._topPromo()

    def _nextGlobalPromo(self):
        promo = self._topPromo()
        nextPromo = self._nextPromo()
        while nextPromo == promo:
            nextPromo = self._nextPromo()
        return promo

    def nextScheduleTicks(self, time):
        if self._promotionsHeap:
            promo = self._nextGlobalPromo()
            while promo <= time:
                promo = self._nextGlobalPromo()
            result = [promo]
        else:
            result = []
        return result

    def schedulerState(self):
        entries = [(j.task, j.releaseIndex) for j in self._readyJobs]
        if self._runningEntry is None:
            runningEntry = None
        else:
            _, job = self._runningEntry
            runningEntry = (job.task, job.releaseIndex)
        return DualPrioritySchedulerState(self._policy,
                                          runningEntry,
                                          *entries)

    def _initFromState(self, schedulerState, jobManager):
        super()._initFromState(schedulerState, jobManager)
        self._policy = schedulerState.policy()

    def addReadyJob(self, job):
        assert job not in self._readyJobs
        self._readyJobs.add(job)

    def _jobPriority(self, job, time):
        relativeTime = time - job.releaseTime
        assert relativeTime >= 0
        priority = self._policy.priorityAt(job.task, relativeTime)
        return priority, job.releaseIndex

    def _topReadyJob(self, time):
        prioritizedJobs = [(self._jobPriority(job, time), job)
                           for job in self._readyJobs]
        priority, topJob = min(prioritizedJobs)
        return priority, topJob

    def schedule(self, time):
        result = ScheduleTransition(None, None)
        if self._readyJobs:
            readyPriority, readyJob = self._topReadyJob(time)
            if self._runningEntry is None:
                self._runningEntry = readyPriority, readyJob
                self._readyJobs.remove(readyJob)
                logger.debug('Scheduling %s from idle', readyJob)
                result = ScheduleTransition(None, readyJob)
            else:
                _, runningJob = self._runningEntry
                runningPriority = self._jobPriority(runningJob, time)
                if readyPriority < runningPriority:
                    self._runningEntry = readyPriority, readyJob
                    self._readyJobs.remove(readyJob)
                    self._readyJobs.add(runningJob)
                    logger.debug('Preemption of %s by %s', runningJob, readyJob)
                    result = ScheduleTransition(runningJob, readyJob)
                else:
                    logger.debug('No schedule change')
                    result = ScheduleTransition(runningJob, runningJob)

        elif self._runningEntry is not None:
            runningPriority, runningJob = self._runningEntry
            logger.debug('No schedule change (no ready job)')
            result = ScheduleTransition(runningJob, runningJob)
        else:
            logger.debug('Nothing to schedule')

        return result

    def __repr__(self):
        readyStr = ', '.join(str(e) for e in self._readyJobs)
        return 'DualPriorityScheduler({}, [{}])'.format(self._runningEntry,
                                                        readyStr)
