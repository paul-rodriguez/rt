
import logging
from bisect import bisect, bisect_left, insort
from abc import ABC, abstractmethod

from .utils.eq import ValueEqual
from .internals.histmaps import DeadlineMissMap, PreemptionMap

logger = logging.getLogger(__name__)


class DeadlineMissFilter(ValueEqual):

    def __init__(self, default, *tasks):
        super().__init__()
        self._default = default
        self._tasks = tuple(tasks)

    def isActive(self):
        if self._default:
            return True
        else:
            return len(self._tasks) > 0

    def match(self, task):
        if task in self._tasks:
            return not self._default
        else:
            return self._default

    def __repr__(self):
        tasksStr = ', '.join(t for t in sorted(self._tasks))
        return 'DeadlineMissFilter({}, [{}])'.format(self._default,
                                                     tasksStr)


class SimulationHistory:

    def __init__(self):
        super().__init__()
        self._stateMap = {}
        self._sortedTimes = []
        self._deadlineMissMap = DeadlineMissMap()
        self._preemptionMap = PreemptionMap()

    def addState(self, state):
        time = state.time
        self._stateMap[time] = state
        self._addStateToMaps(time, state)
        logger.debug('State added at time %d: %s', time, state)

    def _addStateToMaps(self, time, state):
        if time not in self._sortedTimes:
            insort(self._sortedTimes, time)
        self._deadlineMissMap.addState(state)
        self._preemptionMap.addState(state)

    def frozen(self):
        return FrozenHistory(self._stateMap.values())

    def __contains__(self, time):
        index = bisect_left(self._sortedTimes, time)
        return self._sortedTimes[index] == time

    def __getitem__(self, time):
        return self._stateAtTime(time)

    def getLastState(self, time):
        index = bisect(self._sortedTimes, time) - 1
        lastTime = self._sortedTimes[index]
        state = self._stateAtTime(lastTime)
        assert state.time <= time
        return state

    def firstDeadlineMiss(self, dmFilter=True):
        if dmFilter is True:
            dmFilter = DeadlineMissFilter(True)
        elif dmFilter is False:
            dmFilter = DeadlineMissFilter(False)

        return self._deadlineMissMap.firstOccurrence(dmFilter)

    def deadlineMisses(self, timeLimit, **args):
        """
        Get deadline misses that occured until @p timeLimit.

        @p args is passed to DeadlineMissMap.lookup()
        """
        deadlines = self._deadlineMissMap.lookup(**args)
        withinLimit = {d for d in deadlines if d.time <= timeLimit}
        return withinLimit

    def preemptions(self, timeLimit, **args):
        """
        Get preemptions that occured until @p timeLimit.

        @p args is passed to PreemptionMap.lookup()
        """
        preemptions = self._preemptionMap.lookup(**args)
        withinLimit = {p for p in preemptions if p.time <= timeLimit}
        return withinLimit

    def __repr__(self):
        try:
            lastTime = self._sortedTimes[-1]
        except IndexError:
            pass
        else:
            lastState = self._stateAtTime(lastTime)
            return 'History(last time {}, {})'.format(lastTime,
                                                      lastState)
        return 'History(empty)'

    def longRepr(self):
        timeStr = str(self._sortedTimes)
        stateStr = ', '.join(
            [str(self._stateAtTime(t)) for t in self._sortedTimes])
        return 'History(times{}, states[{}]'.format(timeStr, stateStr)

    def _stateMap(self):
        return self._stateMap

    def _stateAtTime(self, time):
        return self._stateMap[time]


class FrozenHistory(SimulationHistory, ValueEqual):

    def __init__(self, states):
        super().__init__()
        for state in states:
            super().addState(state)
        self._stateMap = frozenset(self._stateMap.items())

    def hasDeadlineMiss(self):
        return self.firstDeadlineMiss() is not None

    def lastState(self):
        return self.__getitem__(self.lastTime())

    def lastTime(self):
        return self.stateTimes()[-1]

    def stateTimes(self):
        return list(self._sortedTimes)

    def addState(self, state):
        del state
        raise NotImplementedError

    def frozen(self):
        return self

    def _nonValueFields(self):
        return '_sortedTimes', '_deadlineMissMap', '_preemptionMap'

    def _stateMap(self):
        return dict(self._stateMap)

    def _stateAtTime(self, time):
        for t, state in self._stateMap:
            if t == time:
                return state
        raise AssertionError


class SimulatorState(ValueEqual):

    def __init__(self,
                 time,
                 jobs,
                 events,
                 deadlineMisses=None,
                 preemptions=None,
                 scheduler=None):
        super().__init__()
        self._time = time
        self._jobs = frozenset(jobs)
        self._events = frozenset(events)

        if deadlineMisses is None:
            self._deadlineMisses = frozenset()
        else:
            self._deadlineMisses = frozenset(deadlineMisses)

        if preemptions is None:
            self._preemptions = frozenset()
        else:
            self._preemptions = frozenset(preemptions)

        if scheduler is None:
            self._scheduler = EDFSchedulerState()
        else:
            self._scheduler = scheduler

    @property
    def events(self):
        return self._events

    @property
    def jobs(self):
        return self._jobs

    @property
    def time(self):
        return self._time

    @property
    def scheduler(self):
        return self._scheduler

    @property
    def deadlineMisses(self):
        return self._deadlineMisses

    @property
    def preemptions(self):
        return self._preemptions

    def __repr__(self):
        jobStr = 'jobs[' + ', '.join([str(j) for j in self._jobs]) + ']'
        eventStr = 'events[' + ', '.join([str(e) for e in self.events]) + ']'
        deadlineMissStr = ('deadlineMisses[' +
                           ', '.join([str(m) for m in self._deadlineMisses]) +
                           ']')
        preemptionStr = ('preemptions[' +
                         ', '.join([str(p) for p in self._preemptions]) +
                         ']')
        return 'State({}, {}, {}, {}, {}, {})'.format(self.time,
                                                      self.scheduler,
                                                      jobStr,
                                                      eventStr,
                                                      deadlineMissStr,
                                                      preemptionStr)


class DeadlineMiss(ValueEqual):

    def __init__(self, task, releaseIndex):
        super().__init__()
        self._task = task
        self._releaseIndex = releaseIndex

    @property
    def task(self):
        return self._task

    @property
    def releaseIndex(self):
        return self._releaseIndex

    @property
    def time(self):
        arrival = self._task.arrivalTime(self._releaseIndex)
        deadline = arrival + self._task.deadline
        return deadline

    def __repr__(self):
        return 'DeadlineMiss({}, {})'.format(self._task, self._releaseIndex)


class Preemption(ValueEqual):

    def __init__(self,
                 time,
                 preemptedTask,
                 preemptedIndex,
                 preemptingTask,
                 preemptingIndex,
                 debt=0,
                 previousDebt=0):
        super().__init__()
        self._time = time
        self._preemptedTask = preemptedTask
        self._preemptedIndex = preemptedIndex
        self._preemptingTask = preemptingTask
        self._preemptingIndex = preemptingIndex
        self._debt = debt
        self._previousDebt = previousDebt

    @property
    def time(self):
        return self._time

    @property
    def preemptedTask(self):
        return self._preemptedTask

    @property
    def preemptedIndex(self):
        return self._preemptedIndex

    @property
    def preemptingTask(self):
        return self._preemptingTask

    @property
    def preemptingIndex(self):
        return self._preemptingIndex

    @property
    def debt(self):
        return self._debt

    @property
    def previousDebt(self):
        return self._previousDebt

    @property
    def addedDebt(self):
        return self._debt - self._previousDebt

    def __repr__(self):
        return 'Preemption(T {}, of ({}, {}), by ({}, {}), debt {}' \
               ', prev {})'.format(self._time,
                                   self._preemptedTask,
                                   self._preemptedIndex,
                                   self._preemptingTask,
                                   self._preemptingIndex,
                                   self._debt,
                                   self._previousDebt)


class SchedulerState(ABC, ValueEqual):

    def __init__(self, runningEntry=None, *readyEntries):
        super().__init__()
        self._readyEntries = tuple(self._makeEntry(*e) for e in readyEntries)
        if runningEntry is not None:
            self._runningEntry = self._makeEntry(*runningEntry)
        else:
            self._runningEntry = None

    @abstractmethod
    def _makeEntry(self, *args):
        pass

    @abstractmethod
    def _basicEntry(self, entry):
        pass

    def basicReadyEntries(self):
        return [self._basicEntry(e) for e in self._readyEntries]

    def basicRunningEntry(self):
        return self._basicEntry(self._runningEntry)

    @property
    def readyEntries(self):
        return self._readyEntries

    @property
    def runningEntry(self):
        return self._runningEntry


class EDFSchedulerState(SchedulerState):

    def __init__(self, runningEntry=None, *readyEntries):
        super().__init__(runningEntry, *readyEntries)

    def _basicEntry(self, entry):
        deadline, collision, task, index = entry
        return (deadline, collision), task, index

    def _makeEntry(self, *args):
        if len(args) == 3:
            deadline, task, index = args
            collision = 0
        elif len(args) == 4:
            deadline, collision, task, index = args
        else:
            logger.error('EDFSchedulerState created with an incorrect number '
                         'of parameters: %s', len(args))
            raise ValueError
        return deadline, collision, task, index

    def __repr__(self):
        readyStr = ', '.join([str(e) for e in self._readyEntries])
        return 'EDFSchedulerState({}, ready[{}])'.format(self._runningEntry,
                                                         readyStr)


class RMSchedulerState(SchedulerState):

    def __init__(self, runningEntry=None, *readyEntries):
        super().__init__(runningEntry, *readyEntries)

    def _basicEntry(self, entry):
        task, index = entry
        return (task.minimalInterArrivalTime, task.uniqueId), task, index

    def _makeEntry(self, *args):
        if len(args) == 2:
            task, index = args
        else:
            logger.error('RMSchedulerState created with an incorrect number '
                         'of parameters: %s', len(args))
            raise ValueError
        return task, index

    def __repr__(self):
        readyStr = ', '.join([str(e) for e in self._readyEntries])
        return 'RMSchedulerState({}, ready[{}])'.format(self._runningEntry,
                                                        readyStr)


class DualPrioritySchedulerState(SchedulerState):

    def __init__(self, policy, runningEntry=None, *readyEntries):
        super().__init__(runningEntry, *readyEntries)
        self._policy = policy

    def _basicEntry(self, entry):
        task, index = entry
        return (task.minimalInterArrivalTime, task.uniqueId), task, index

    def _makeEntry(self, *args):
        if len(args) == 2:
            task, index = args
        else:
            logger.error('DualPrioritySchedulerState created with an '
                         'incorrect number of entry parameters: %s',
                         len(args))
            raise ValueError
        return task, index

    def policy(self):
        return self._policy

    def __repr__(self):
        fmtStr = 'DualPrioritySchedulerState({}, {}, ready[{}])'
        readyStr = ', '.join([str(e) for e in self._readyEntries])
        return fmtStr.format(self._policy,
                             self._runningEntry,
                             readyStr)


class JobState(ValueEqual):

    def __init__(self,
                 task,
                 releaseIndex=0,
                 progress=0,
                 preemptionDebt=0,
                 lastStart=None):
        super().__init__()
        self._task = task
        self._index = releaseIndex
        self._progress = progress
        self._preemptionDebt = preemptionDebt
        self._lastStart = lastStart

    @property
    def releaseTime(self):
        return self._task.arrivalTime(self._index)

    @property
    def releaseIndex(self):
        return self._index

    @property
    def task(self):
        return self._task

    @property
    def lastStart(self):
        return self._lastStart

    @property
    def remainingWcet(self):
        return self._task.wcet - self._progress

    @property
    def progress(self):
        return self._progress

    @property
    def preemptionDebt(self):
        return self._preemptionDebt

    def __repr__(self):
        return 'JobState({}, I {}, P {}, D {}, L {})'.format(
            self._task,
            self._index,
            self._progress,
            self._preemptionDebt,
            self._lastStart)


class StateEvent(ABC, ValueEqual):

    def __init__(self, time):
        super().__init__()
        self._time = time

    @property
    def time(self):
        return self._time


class StateArrival(StateEvent):

    def __init__(self, time, task, releaseIndex):
        super().__init__(time)
        self._task = task
        self._releaseIndex = releaseIndex

    @property
    def task(self):
        return self._task

    @property
    def releaseIndex(self):
        return self._releaseIndex

    def __repr__(self):
        return 'Arrival({}, {}, {})'.format(self.time,
                                            self._task,
                                            self._releaseIndex)


class StateCompletion(StateEvent):

    def __init__(self, time, task, releaseIndex):
        super().__init__(time)
        self._task = task
        self._releaseIndex = releaseIndex

    @property
    def task(self):
        return self._task

    @property
    def releaseIndex(self):
        return self._releaseIndex

    def __repr__(self):
        return 'Completion({}, {}, {})'.format(self.time,
                                               self._task,
                                               self._releaseIndex)


class StateDeadline(StateEvent):

    def __init__(self, time, task, releaseIndex):
        super().__init__(time)
        self._task = task
        self._releaseIndex = releaseIndex

    @property
    def task(self):
        return self._task

    @property
    def releaseIndex(self):
        return self._releaseIndex

    def __repr__(self):
        return 'Deadline({}, {}, {})'.format(self.time,
                                             self._task,
                                             self._releaseIndex)


class StateScheduleTick(StateEvent):

    def __init__(self, time):
        super().__init__(time)

    def __repr__(self):
        return 'ScheduleTick({})'.format(self.time)
