
from crpd.model import (Task, Taskset, FixedArrivalDistribution,
                        LogPreemptionCost, FixedPreemptionCost)
from crpd.sim import SimulationSetup, SimulationRun
from crpd.stats import SimulationStatistics, AggregatorTag


def test_preemptionTimeAggregator():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    FixedPreemptionCost(2),
                    displayName='long')
    shortTask = Task(1,
                     5,
                     FixedArrivalDistribution(5),
                     FixedPreemptionCost(2),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    setup = SimulationSetup(taskset,
                            time=29,
                            aggregatorTags=[AggregatorTag.PreemptionTime])
    run = SimulationRun(setup)
    result = run.result()
    aggregatePreemptTime = result.aggregateStat(AggregatorTag.PreemptionTime)
    assert aggregatePreemptTime == 10


def test_preemptionNbAggregator():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    FixedPreemptionCost(2),
                    displayName='long')
    shortTask = Task(1,
                     5,
                     FixedArrivalDistribution(5),
                     FixedPreemptionCost(2),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    setup = SimulationSetup(taskset,
                            time=29,
                            aggregatorTags=[AggregatorTag.PreemptionCount])
    run = SimulationRun(setup)
    result = run.result()
    aggregateNbPreempt = result.aggregateStat(AggregatorTag.PreemptionCount)
    assert aggregateNbPreempt == 5


def test_executionTimeStats():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    displayName='long')
    shortTask = Task(1,
                     5,
                     FixedArrivalDistribution(5),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    setup = SimulationSetup(taskset,
                            time=29)
    run = SimulationRun(setup)
    result = run.result()
    stats = SimulationStatistics(result)
    execTime = stats.totalExecutionTime()
    assert execTime == 26


def test_executionTimeAggregator():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    displayName='long')
    shortTask = Task(1,
                     5,
                     FixedArrivalDistribution(5),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    setup = SimulationSetup(taskset,
                            time=29,
                            aggregatorTags=[AggregatorTag.ExecutionTime])
    run = SimulationRun(setup)
    result = run.result()
    aggregateExecTime = result.aggregateStat(AggregatorTag.ExecutionTime)
    assert aggregateExecTime == 26


def test_freePreemptionsTotals():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    displayName='long')
    shortTask = Task(1,
                     5,
                     FixedArrivalDistribution(5),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    setup = SimulationSetup(taskset, time=50, trackPreemptions=True)
    run = SimulationRun(setup)
    result = run.result()
    stats = SimulationStatistics(result)
    nbPreemptions = stats.nbOfPreemptions
    expectedNbPreemptions = 4
    preemptionCost = stats.totalPreemptionTime
    expectedPreemptionCost = 0

    assert nbPreemptions == expectedNbPreemptions
    assert preemptionCost == expectedPreemptionCost


def test_logPreemptionsTotals():
    longTask = Task(2000,
                    5000,
                    FixedArrivalDistribution(5000),
                    LogPreemptionCost(1, 0.1),
                    displayName='long')
    shortTask = Task(100,
                     500,
                     FixedArrivalDistribution(500),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    setup = SimulationSetup(taskset, time=5000, trackPreemptions=True)
    run = SimulationRun(setup)
    result = run.result()
    stats = SimulationStatistics(result)
    nbPreemptions = stats.nbOfPreemptions
    expectedNbPreemptions = 6
    preemptionCost = stats.totalPreemptionTime
    expectedPreemptionCost = 685

    assert nbPreemptions == expectedNbPreemptions
    assert preemptionCost == expectedPreemptionCost
