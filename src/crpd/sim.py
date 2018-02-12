
import logging
from enum import Enum

from .policy import EDFSchedulingPolicy
from .utils.eq import ValueEqual
from .hist import (DeadlineMissFilter,
                   SimulationHistory,
                   SimulatorState,
                   StateArrival)
from .internals.simulator import Simulator
from .internals.sched import (DualPriorityScheduler,
                              EDFScheduler,
                              RMScheduler,
                              SchedulerFactory)
from .internals.errors import SimulationError
from .utils.persistence import FileEnv
from .stats import StatAggregator

logger = logging.getLogger(__name__)

DEFAULT_TIME_LIMIT = 10**100


class SimulationSetup(ValueEqual):
    """
    A complete representation of the parameters of a simulation, including
    taskset, time limit and scheduling algorithm.
    """

    def __init__(self,
                 taskset,
                 time=1000,
                 schedulingPolicy=None,
                 deadlineMissFilter=False,
                 trackHistory=True,
                 trackPreemptions=True,
                 aggregatorTags=None):
        super().__init__()
        self._taskset = taskset
        self._time = time
        self._trackHistory = trackHistory
        self._trackPreemptions = trackPreemptions

        if schedulingPolicy is None:
            self._schedulingPolicy = EDFSchedulingPolicy()
        else:
            self._schedulingPolicy = schedulingPolicy

        if deadlineMissFilter is False:
            self._deadlineMissFilter = DeadlineMissFilter(False)
        elif deadlineMissFilter is True:
            self._deadlineMissFilter = DeadlineMissFilter(True)
        else:
            self._deadlineMissFilter = deadlineMissFilter

        if aggregatorTags is None:
            self._aggregatorTags = tuple()
        else:
            self._aggregatorTags = tuple(aggregatorTags)

    @property
    def taskset(self):
        return self._taskset

    @property
    def time(self):
        return self._time

    @property
    def deadlineMissFilter(self):
        return self._deadlineMissFilter

    @property
    def trackHistory(self):
        return self._trackHistory

    @property
    def trackPreemptions(self):
        return self._trackPreemptions

    @property
    def schedulingPolicy(self):
        return self._schedulingPolicy

    @property
    def aggregatorTags(self):
        return self._aggregatorTags

    def __repr__(self):
        formatStr = ('SimulationSetup({}, time={}, trackHistory={}, '
                     'trackPreemptions={}, '
                     'deadlineMissFilter={}, schedulingPolicy={}, '
                     'aggregatorTags=[{}])')
        aggregatorStr = ', '.join('AggregatorTag.' + ag.name
                                  for ag in self._aggregatorTags)
        return formatStr.format(self._taskset,
                                self._time,
                                self._trackHistory,
                                self._trackPreemptions,
                                self._deadlineMissFilter,
                                self._schedulingPolicy,
                                aggregatorStr)


class SimulationRun(ValueEqual):
    """
    Encapsulates the definition and execution of a simulation run.
    """

    def __init__(self, setup, errorHandling=True):
        super().__init__()
        self._setup = setup
        self._aggregators = self._createAggregators()
        self._sim = None
        self._result = None
        self._errorHandling = errorHandling
        if errorHandling:
            self._logsEnv = FileEnv('errorLogs')

    @property
    def setup(self):
        return self._setup

    @property
    def time(self):
        return self._setup.time

    @property
    def history(self):
        return self.result().history

    def getState(self, time):
        self.execute()
        assert time <= self._setup.time
        return self._sim.getState(time)

    def result(self):
        if self._result is None:
            self.execute()
            self._result = SimulationResult(self._setup,
                                            self._sim.history.frozen(),
                                            self._aggregators)
        return self._result

    def execute(self):
        if self._sim is None:
            try:
                self._sim = Simulation(
                    self._setup.taskset,
                    self._setup.schedulingPolicy,
                    trackHistory=self._setup.trackHistory,
                    trackPreemptions=self._setup.trackPreemptions,
                    aggregators=self._aggregators)
                dmFilter = self._setup.deadlineMissFilter
                if dmFilter.isActive():
                    self._sim.firstDeadlineMiss(dmFilter, self._setup.time)
                else:
                    self._sim.getState(self._setup.time)
            except AssertionError as e:
                if self._errorHandling:
                    simuError = SimulationError('Assertion failed: ' + str(e),
                                                self._setup,
                                                self.history)
                    simuError.saveToFile()
                else:
                    raise
            except SimulationError as e:
                if self._errorHandling:
                    e.saveToFile()
                else:
                    raise
            except NotImplementedError as e:
                if self._errorHandling:
                    simuError = SimulationError(
                        'Not implemented error: ' + str(e),
                        self._setup,
                        self.history)
                    simuError.saveToFile()
                else:
                    raise

    def _createAggregators(self):
        return [StatAggregator.createInstance(tag)
                for tag in self._setup.aggregatorTags]

    def _nonValueFields(self):
        return '_sim', '_aggregators', '_result'


class SimulationResult(ValueEqual):
    """
    The result of a simulation run.
    """

    def __init__(self, setup, history, aggregators):
        super().__init__()
        self._setup = setup
        self._history = history.frozen()
        self._aggregateStats = tuple(self._createStats(aggregators))

    @property
    def time(self):
        return self._setup.time

    @property
    def setup(self):
        return self._setup

    @property
    def history(self):
        return self._history

    def aggregateStat(self, key):
        for k, v in self._aggregateStats:
            if key == k:
                return v
        raise AssertionError('Aggregate statistic not available '
                             '(add it to the setup)')

    @staticmethod
    def _createStats(aggregators):
        for aggregator in aggregators:
            yield aggregator.key(), aggregator.result()


class Simulation:
    """
    Represents a simulation of a task set.

    Use the getState() function to obtain the state of the simulation at the
    desired time.
    The state is lazily constructed.
    """

    def __init__(self,
                 taskset,
                 schedulingPolicy=None,
                 trackHistory=True,
                 trackPreemptions=True,
                 aggregators=None):
        self._taskset = taskset
        self._trackHistory = trackHistory
        self._trackPreemptions = trackPreemptions
        self._history = SimulationHistory()

        if schedulingPolicy is None:
            self._schedulingPolicy = EDFSchedulingPolicy()
        else:
            self._schedulingPolicy = schedulingPolicy

        self._createInitialState()

        if aggregators is None:
            self._aggregators = tuple()
        else:
            self._aggregators = tuple(aggregators)

    def firstDeadlineMiss(self, dmFilter=True, timeLimit=DEFAULT_TIME_LIMIT):
        if dmFilter is True:
            dmFilter = DeadlineMissFilter(True)
        elif dmFilter is False:
            dmFilter = DeadlineMissFilter(False)

        historyDeadlineMiss = self._history.firstDeadlineMiss(dmFilter)
        if historyDeadlineMiss is None:
            state = self._history.getLastState(timeLimit)
            newState = self._buildAndRunSimu(state, timeLimit, True)
            return newState
        else:
            return historyDeadlineMiss

    def getState(self, time):
        lastState = self._history.getLastState(time)
        if lastState.time < time:
            newState = self._buildAndRunSimu(lastState, time, False)
            return newState
        else:
            return lastState

    @property
    def taskset(self):
        return self._taskset

    @property
    def history(self):
        return self._history

    def deadlineMisses(self, timeLimit, **args):
        self.getState(timeLimit)
        return self._history.deadlineMisses(timeLimit, **args)

    def preemptions(self, timeLimit, **args):
        self.getState(timeLimit)
        return self._history.preemptions(timeLimit, **args)

    def noDeadlineMiss(self, timeLimit):
        self.getState(timeLimit)
        return len(self.deadlineMisses(timeLimit)) == 0

    def _buildAndRunSimu(self, initState, time, stopOnMiss):
        simulator = Simulator(self._taskset,
                              self._history,
                              initState,
                              trackHistory=self._trackHistory,
                              trackPreemptions=self._trackPreemptions,
                              statAggregators=self._aggregators)
        simulator.simulateTo(time, stopOnMiss=stopOnMiss)
        newState = self._history.getLastState(time)
        return newState

    def _createInitialState(self):
        arrivals = [StateArrival(0, task, 0) for task in self._taskset]
        scheduler = SchedulerFactory.fromPolicy(self._schedulingPolicy)
        initState = SimulatorState(0,
                                   [],
                                   arrivals,
                                   scheduler=scheduler.schedulerState())
        self._history.addState(initState)
