from tempfile import TemporaryDirectory

from .loggers import eqLog
from crpd.model import (Task, Taskset, FixedArrivalDistribution,
                        PoissonArrivalDistribution, LogPreemptionCost,
                        FixedPreemptionCost)
from crpd.hist import (SimulatorState, EDFSchedulerState, JobState,
                       StateDeadline, StateArrival, StateCompletion,
                       SimulationHistory)
from crpd.sim import (SimulationSetup, SimulationRun)
from crpd.utils.persistence import FileEnv, MemoryEnv


def test_fileInventory():
    item1 = FixedArrivalDistribution(3)
    item2 = FixedPreemptionCost(2)

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir, manifest=True)
        item1Key = 'testitem1'
        item2Key = 'testitem2'
        itemSet = {(item1Key, item1),
                   (item2Key, item2)}
        dataEnv.save(item1, item1Key)
        dataEnv.save(item2, item2Key)
        copySet = set(dataEnv.items())
    assert (copySet == itemSet)
    assert (dataEnv.keys() == {item1Key, item2Key})


def test_inventoryLoading():
    item1 = FixedArrivalDistribution(3)
    item2 = FixedPreemptionCost(2)

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir, manifest=True)
        item1Key = 'testitem1'
        item2Key = 'testitem2'
        itemSet = {(item1Key, item1),
                   (item2Key, item2)}
        dataEnv.save(item1, item1Key)
        dataEnv.save(item2, item2Key)

        dataEnv2 = FileEnv(testdir, manifest=True)
        copySet = set(dataEnv2.items())
        assert (copySet == itemSet)
        assert (dataEnv2.keys() == {item1Key, item2Key})


def test_saveSimpleObject():
    item = FixedArrivalDistribution(3)

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        itemKey = 'testitem'
        dataEnv.save(item, itemKey)
        copy = dataEnv.load(itemKey)
    assert (copy == item)


def test_saveTaskset():
    t1 = Task(1, 2, FixedArrivalDistribution(3), LogPreemptionCost(1, 0.1))
    t2 = Task(4, 5, PoissonArrivalDistribution(6, 2), FixedPreemptionCost(3))
    taskset = Taskset(t1, t2)

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        tasksetKey = 'testtaskset'
        dataEnv.save(taskset, tasksetKey)
        copy = dataEnv.load(tasksetKey)
    assert(copy == taskset)


def test_memoryEnv():
    t1 = Task(1, 2, FixedArrivalDistribution(3), LogPreemptionCost(1, 0.1))
    t2 = Task(4, 5, PoissonArrivalDistribution(6, 2), FixedPreemptionCost(3))
    taskset = Taskset(t1, t2)
    state = SimulatorState(82000,
                           [JobState(t1, 55, preemptionDebt=1515),
                            JobState(t2, 66, lastStart=42)],
                           [StateDeadline(77, t1, 2),
                            StateArrival(88, t2, 3),
                            StateCompletion(99, t1, 4)],
                           scheduler=EDFSchedulerState((1043, t1, 1001),
                                                       (1042, t2, 1002)))
    dataEnv = MemoryEnv()
    stateKey = 'teststate'
    tasksetKey = 'testtaskset'
    dataEnv.save(state, stateKey)
    dataEnv.save(taskset, tasksetKey)
    stateCopy = dataEnv.load(stateKey)
    tasksetCopy = dataEnv.load(tasksetKey)
    assert(state == stateCopy)
    assert(taskset == tasksetCopy)


def test_simulationResult():
    t1 = Task(1, 2, FixedArrivalDistribution(3), LogPreemptionCost(1, 0.1),
              displayName='t1')
    t2 = Task(4, 5, PoissonArrivalDistribution(6, 2), FixedPreemptionCost(3),
              displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=200)
    run = SimulationRun(setup)
    result = run.result()

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(result, key)
        copy = dataEnv.load(key)
    assert(copy == result)


def test_saveSimulationSetup():
    t1 = Task(1, 2, FixedArrivalDistribution(3), displayName='t1')
    t2 = Task(4, 5, FixedArrivalDistribution(6), displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=200)

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(setup, key)
        copy = dataEnv.load(key)
    assert(copy == setup)


def test_saveSimulationResult():
    t1 = Task(1, 2, FixedArrivalDistribution(3), LogPreemptionCost(1, 0.1),
              displayName='t1')
    t2 = Task(4, 5, PoissonArrivalDistribution(6, 2), FixedPreemptionCost(3),
              displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=200)
    run = SimulationRun(setup)
    result = run.result()

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(result, key)
        copy = dataEnv.load(key)
    assert(copy == result)


def test_saveFrozenHistory():
    t1 = Task(1, 2, FixedArrivalDistribution(3), LogPreemptionCost(1, 0.1),
              displayName='t1')
    t2 = Task(4, 5, PoissonArrivalDistribution(6, 2), FixedPreemptionCost(3),
              displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=5)
    run = SimulationRun(setup)
    result = run.result()
    history = result.history

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(history, key)
        copy = dataEnv.load(key)

    assert(copy == history)


def test_saveSmallSimulatorState():
    state = SimulatorState(10, [], [])

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(state, key)
        copy = dataEnv.load(key)

    assert(copy == state)


def test_saveSmallFrozenHistory():
    history = SimulationHistory()
    history.addState(SimulatorState(10, [], []))
    frozen = history.frozen()

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(frozen, key)
        copy = dataEnv.load(key)

    assert(copy == frozen)


def test_saveEmptyFrozenHistory():
    history = SimulationHistory().frozen()

    with TemporaryDirectory() as testdir:
        dataEnv = FileEnv(testdir)
        key = 'test'
        dataEnv.save(history, key)
        copy = dataEnv.load(key)

    assert(copy == history)
