import logging
import pytest

from crpd.sim import SimulationSetup
from crpd.hist import (SimulatorState, EDFSchedulerState,
                       JobState, StateCompletion, StateArrival,
                       StateDeadline)
from crpd.model import Task, Taskset, FixedArrivalDistribution
from crpd.runner import simulationRunner


@pytest.mark.skip
def test_monocoreRun():
    t1 = Task(1, 10, FixedArrivalDistribution(10), displayName='t')
    setup = SimulationSetup(Taskset(t1), time=1000, trackHistory=True)
    setups = [setup]
    runner = simulationRunner(setups, multicore=False)
    runner.start()
    runner.join()
    result = runner.result(setup)
    expectedStates = [
        (10, SimulatorState(
            10,
            [JobState(t1, 1, lastStart=10),
             JobState(t1, 2)],
            [StateCompletion(11, t1, 1),
             StateArrival(20, t1, 2),
             StateDeadline(20, t1, 1)],
            scheduler=EDFSchedulerState((20, t1, 1)))),
        (987, SimulatorState(
            981,
            [JobState(t1, 98, 1, lastStart=981),
             JobState(t1, 99)],
            [StateArrival(990, t1, 99),
             StateDeadline(990, t1, 98)],
            scheduler=EDFSchedulerState()))
    ]

    for time, expected in expectedStates:
        state = result.history.getLastState(time)

        logging.debug('Expected  %s', expected)
        logging.debug('Effective %s', state)
        assert (state == expected)


@pytest.mark.skip
def test_simpleRun():
    t1 = Task(1, 10, FixedArrivalDistribution(10), displayName='t')
    setup = SimulationSetup(Taskset(t1), time=1000, trackHistory=True)
    setups = [setup]
    runner = simulationRunner(setups)
    runner.start()
    runner.join()
    result = runner.result(setup)
    expectedStates = [
        (10, SimulatorState(
            10,
            [JobState(t1, 1, lastStart=10),
             JobState(t1, 2)],
            [StateCompletion(11, t1, 1),
             StateArrival(20, t1, 2),
             StateDeadline(20, t1, 1)],
            scheduler=EDFSchedulerState((20, t1, 1)))),
        (987, SimulatorState(
            981,
            [JobState(t1, 98, 1, lastStart=981),
             JobState(t1, 99)],
            [StateArrival(990, t1, 99),
             StateDeadline(990, t1, 98)],
            scheduler=EDFSchedulerState()))
    ]

    for time, expected in expectedStates:
        state = result.history.getLastState(time)

        logging.debug('Expected  %s', expected)
        logging.debug('Effective %s', state)
        assert (state == expected)


@pytest.mark.skip
def test_twoTasksets():
    t1 = Task(1, 10, FixedArrivalDistribution(10), displayName='t1')
    t2 = Task(2, 5, FixedArrivalDistribution(5), displayName='t2')
    setup1 = SimulationSetup(Taskset(t1), time=1000)
    setup2 = SimulationSetup(Taskset(t1, t2), time=1000)
    tasksets = [setup1, setup2]
    runner = simulationRunner(tasksets)
    runner.start()
    runner.join()
    result2 = runner.result(setup2)
    result1 = runner.result(setup1)

    endTime = 987
    expected1 = SimulatorState(981,
                               [JobState(t1, 98, 1, lastStart=981),
                                JobState(t1, 99)],
                               [StateArrival(990, t1, 99),
                                StateDeadline(990, t1, 98)],
                               scheduler=EDFSchedulerState())
    expected2 = SimulatorState(endTime,
                               [JobState(t2, 198),
                                JobState(t1, 98, 1, lastStart=983),
                                JobState(t2, 197, 2, lastStart=987),
                                JobState(t1, 99)],
                               [StateDeadline(990, t1, 98),
                                StateDeadline(990, t2, 197),
                                StateArrival(990, t1, 99),
                                StateArrival(990, t2, 198)],
                               scheduler=EDFSchedulerState())

    state1 = result1.history.getLastState(endTime)
    logging.debug('Expected  %s', expected1)
    logging.debug('Effective %s', state1)
    assert (state1 == expected1)

    state2 = result2.history.getLastState(endTime)
    logging.debug('Expected  %s', expected2)
    logging.debug('Effective %s', state2)
    assert (state2 == expected2)
