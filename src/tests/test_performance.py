
import pytest

from .loggers import statsLog
from crpd.model import LogPreemptionCost
from crpd.gen import TasksetGenerator, RandomValue
from crpd.stats import AggregatorTag, SimulationStatistics
from crpd.sim import SimulationSetup, SimulationRun

perf = pytest.mark.skipif(
    not pytest.config.getoption("--runperf"),
    reason="need --runperf option to run")


def genSetups(nbTasksets, aggregators):
    preemptionCost = RandomValue(
        generator=lambda: LogPreemptionCost(3, 0.1))
    gen = TasksetGenerator(seed=1337,
                           scale=100,
                           nbTasks=RandomValue(value=5),
                           period=RandomValue(logRange=(10, 1000)),
                           preemptionCost=preemptionCost,
                           utilization=RandomValue(floatrange=(0.6, 1)))
    tasksets = [gen() for _ in range(nbTasksets)]

    for taskset in tasksets:
        yield SimulationSetup(taskset,
                              time=10000000,
                              trackHistory=False,
                              trackPreemptions=False,
                              deadlineMissFilter=True,
                              aggregatorTags=aggregators)


@perf
def test_simulationWithAggregators():
    aggregators = (AggregatorTag.PreemptionTime,
                   AggregatorTag.ExecutionTime,
                   AggregatorTag.PreemptionCount)

    for setup in genSetups(50, aggregators):
        run = SimulationRun(setup)
        run.execute()


@perf
def test_simulationWithExecTimeStats():
    for setup in genSetups(50, ()):
        run = SimulationRun(setup)
        result = run.result()
        stats = SimulationStatistics(result)
        stats.totalExecutionTime()


@perf
def test_simulationWithoutAggregators():
    aggregators = None

    for setup in genSetups(50, aggregators):
        run = SimulationRun(setup)
        run.execute()
