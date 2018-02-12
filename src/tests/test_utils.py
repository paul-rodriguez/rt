
import pytest
import logging
from .loggers import eqLog

from crpd.policy import SchedulerTag
from crpd.sim import SimulationSetup
from crpd.model import Taskset, Task, FixedArrivalDistribution
from crpd.hist import (JobState, RMSchedulerState, StateArrival, StateDeadline,
                       StateCompletion, SimulatorState)


def test_taskEq():
    task = Task(6293, 17199, FixedArrivalDistribution(17199), uniqueId=0)
    taskCopy = Task(6293, 17199, FixedArrivalDistribution(17199), uniqueId=0)
    assert task == taskCopy


def test_tasksetEq():
    taskset = Taskset(
        Task(6293, 17199, FixedArrivalDistribution(17199), uniqueId=0))
    tasksetCopy = Taskset(
        Task(6293, 17199, FixedArrivalDistribution(17199), uniqueId=0))
    assert taskset == tasksetCopy


def test_complexSetupEquality():
    taskset = Taskset(
        Task(6293, 17199, FixedArrivalDistribution(17199), uniqueId=0),
        Task(1952, 11655, FixedArrivalDistribution(11655), uniqueId=1),
        Task(284, 5391, FixedArrivalDistribution(5391), uniqueId=2),
        Task(475, 14844, FixedArrivalDistribution(14844), uniqueId=3),
        Task(820, 2144, FixedArrivalDistribution(2144), uniqueId=4))
    tasksetCopy = Taskset(
        Task(6293, 17199, FixedArrivalDistribution(17199), uniqueId=0),
        Task(1952, 11655, FixedArrivalDistribution(11655), uniqueId=1),
        Task(284, 5391, FixedArrivalDistribution(5391), uniqueId=2),
        Task(475, 14844, FixedArrivalDistribution(14844), uniqueId=3),
        Task(820, 2144, FixedArrivalDistribution(2144), uniqueId=4))
    setup = SimulationSetup(taskset,
                            time=10000000,
                            schedulingPolicy=SchedulerTag.EDF,
                            deadlineMissFilter=False,
                            trackHistory=False)
    setupCopy = SimulationSetup(tasksetCopy,
                                time=10000000,
                                schedulingPolicy=SchedulerTag.EDF,
                                deadlineMissFilter=False,
                                trackHistory=False)
    assert setup == setupCopy


def test_setupEquality():
    taskset1 = Taskset(Task(10, 10, FixedArrivalDistribution(10), uniqueId=0))
    taskset2 = Taskset(Task(10, 10, FixedArrivalDistribution(10), uniqueId=0))
    taskset3 = Taskset(Task(9, 10, FixedArrivalDistribution(10)))
    setup1 = SimulationSetup(taskset=taskset1, schedulingPolicy=SchedulerTag.EDF)
    setup2 = SimulationSetup(taskset=taskset2, schedulingPolicy=SchedulerTag.EDF)
    setup3 = SimulationSetup(taskset=taskset3, schedulingPolicy=SchedulerTag.EDF)

    logging.debug(hash(setup1))
    logging.debug(hash(setup2))
    logging.debug(hash(setup3))
    assert setup1 == setup2
    assert setup2 == setup1
    assert setup2 != setup3


def test_jobStateEq():
    t1 = Task(1, 1, FixedArrivalDistribution(1))
    js1 = JobState(t1, 1, 1)
    js2 = JobState(t1, 1, 1)
    js3 = JobState(t1, 2, 2)

    logging.debug(hash(js1))
    logging.debug(hash(js2))
    logging.debug(hash(js3))

    assert js1 == js2
    assert js1 != js3


def test_eventStateEq():
    t1 = Task(1, 1, FixedArrivalDistribution(1))
    es1 = StateArrival(0, t1, 0)
    es2 = StateArrival(0, t1, 0)
    es3 = StateArrival(1, t1, 1)

    logging.debug(hash(es1))
    logging.debug(hash(es2))
    logging.debug(hash(es3))

    assert es1 == es2
    assert es1 != es3


def test_schedulerStateEq():
    t1 = Task(1, 1, FixedArrivalDistribution(1))
    schedS1 = RMSchedulerState((0, t1))
    schedS2 = RMSchedulerState((0, t1))
    schedS3 = RMSchedulerState((1, t1))

    logging.debug(hash(schedS1))
    logging.debug(hash(schedS2))
    logging.debug(hash(schedS3))

    assert schedS1 == schedS2
    assert schedS1 != schedS3


def test_stateEquality():
    t1 = Task(9, 10, FixedArrivalDistribution(10))
    t2 = Task(9, 10, FixedArrivalDistribution(5))
    state1 = SimulatorState(50,
                            [JobState(t2, 1, 2)],
                            [StateCompletion(25, t1, 12)],
                            scheduler=RMSchedulerState())
    state2 = SimulatorState(50,
                            [JobState(t2, 1, 2)],
                            [StateCompletion(25, t1, 12)],
                            scheduler=RMSchedulerState())
    logging.debug(hash(state1))
    logging.debug(hash(state2))
    assert state1 == state2
