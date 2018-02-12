
import logging

from crpd.model import (Taskset, Task, FixedArrivalDistribution,
                        PoissonArrivalDistribution, FixedPreemptionCost,
                        LogPreemptionCost)
from crpd.policy import (RMSchedulingPolicy,
                         EDFSchedulingPolicy,
                         DualPrioritySchedulingPolicy)
from crpd.sim import Simulation, SimulationSetup
from crpd.stats import AggregatorTag
from crpd.hist import (SimulatorState, JobState, StateCompletion,
                       StateArrival, StateDeadline, EDFSchedulerState,
                       DeadlineMiss, Preemption, RMSchedulerState)
from crpd.runner import SimulationRun
from .loggers import histLog, schedLog, simulatorLog


def test_simuError2():
    taskset = Taskset(Task(103, 1950, FixedArrivalDistribution(1950),
                           LogPreemptionCost(3, 0.1)),
                      Task(109, 1287, FixedArrivalDistribution(1287),
                           LogPreemptionCost(3, 0.1)),
                      Task(13, 4976, FixedArrivalDistribution(4976),
                           LogPreemptionCost(3, 0.1)),
                      Task(380, 1925, FixedArrivalDistribution(1925),
                           LogPreemptionCost(3, 0.1)),
                      Task(817, 1292, FixedArrivalDistribution(1292),
                           LogPreemptionCost(3, 0.1)))

    setup = SimulationSetup(taskset,
                            time=1000000,
                            trackHistory=False,
                            trackPreemptions=False,
                            deadlineMissFilter=True,
                            schedulingPolicy=EDFSchedulingPolicy())
    run = SimulationRun(setup, errorHandling=False)
    run.execute()


def test_simuError1():
    taskset = Taskset(
        Task(45,
             6588,
             FixedArrivalDistribution(6588),
             LogPreemptionCost(3, 0.1)),
        Task(1,
             1036,
             FixedArrivalDistribution(1036),
             LogPreemptionCost(3, 0.1)),
        Task(278,
             1037, FixedArrivalDistribution(1037),
             LogPreemptionCost(3, 0.1)),
        Task(371,
             4148,
             FixedArrivalDistribution(4148),
             LogPreemptionCost(3, 0.1)),
        Task(1412,
             2680,
             FixedArrivalDistribution(2680),
             LogPreemptionCost(3, 0.1)),
    )

    setup = SimulationSetup(taskset,
                            time=1000000,
                            trackHistory=False,
                            trackPreemptions=False,
                            deadlineMissFilter=True,
                            schedulingPolicy=EDFSchedulingPolicy(),
                            aggregatorTags=[AggregatorTag.PreemptionTime,
                                            AggregatorTag.PreemptionCount])

    run = SimulationRun(setup, errorHandling=False)
    run.execute()


def test_rmMiss():
    taskset = Taskset(Task(10649, 72784, FixedArrivalDistribution(72784)),
                      Task(1868, 7242, FixedArrivalDistribution(7242)),
                      Task(8881, 30350, FixedArrivalDistribution(30350)),
                      Task(365, 2047, FixedArrivalDistribution(2047)),
                      Task(1202, 18528, FixedArrivalDistribution(18528)))
    setup = SimulationSetup(taskset,
                            time=10000000,
                            trackHistory=False,
                            deadlineMissFilter=True,
                            schedulingPolicy=RMSchedulingPolicy())
    run = SimulationRun(setup)
    result = run.result()
    assert result.history.hasDeadlineMiss()


def test_edfMiss(schedLog):
    taskset = Taskset(Task(7121, 15449, FixedArrivalDistribution(15449)),
                      Task(1116, 8353, FixedArrivalDistribution(8353)),
                      Task(16554, 82248, FixedArrivalDistribution(82248)),
                      Task(6318, 39033, FixedArrivalDistribution(39033)),
                      Task(180, 4240, FixedArrivalDistribution(4240)))

    endTime = 1000000
    setup = SimulationSetup(taskset,
                            time=endTime,
                            trackHistory=False,
                            deadlineMissFilter=True,
                            schedulingPolicy=EDFSchedulingPolicy())
    run = SimulationRun(setup)
    result = run.result()
    assert not result.history.hasDeadlineMiss()


def test_noTracking():
    t1 = Task(1, 2, FixedArrivalDistribution(2), displayName='t1')
    t2 = Task(10, 20, FixedArrivalDistribution(20), displayName='t2')
    taskset = Taskset(t1, t2)
    endTime = 25
    setup = SimulationSetup(taskset,
                            time=endTime,
                            schedulingPolicy=RMSchedulingPolicy(),
                            trackHistory=False)
    run = SimulationRun(setup)
    result = run.result()
    state = result.history[endTime]
    expected = SimulatorState(endTime,
                              [JobState(t2, 1, 2),
                               JobState(t2, 2),
                               JobState(t1, 12, 1, lastStart=25),
                               JobState(t1, 13)],
                              [StateCompletion(25, t1, 12),
                               StateDeadline(40, t2, 1),
                               StateCompletion(31, t2, 1),
                               StateArrival(26, t1, 13),
                               StateDeadline(26, t1, 12),
                               StateArrival(40, t2, 2),
                               StateCompletion(32, t2, 1)],
                              scheduler=RMSchedulerState((t1, 12), (t2, 1)))
    assert state == expected


def test_rmMultiple():
    t1 = Task(1, 2, FixedArrivalDistribution(2), displayName='t1')
    t2 = Task(10, 20, FixedArrivalDistribution(20), displayName='t2')
    taskset = Taskset(t1, t2)
    endTime = 25
    setup = SimulationSetup(taskset,
                            time=endTime,
                            schedulingPolicy=RMSchedulingPolicy())
    run = SimulationRun(setup)
    result = run.result()
    state = result.history[endTime]
    expected = SimulatorState(endTime,
                              [JobState(t2, 1, 2),
                               JobState(t2, 2),
                               JobState(t1, 12, 1, lastStart=25),
                               JobState(t1, 13)],
                              [StateCompletion(25, t1, 12),
                               StateDeadline(40, t2, 1),
                               StateCompletion(31, t2, 1),
                               StateArrival(26, t1, 13),
                               StateDeadline(26, t1, 12),
                               StateArrival(40, t2, 2),
                               StateCompletion(32, t2, 1)],
                              scheduler=RMSchedulerState((t1, 12), (t2, 1)))
    assert(state == expected)


def test_rmIsBad():
    t1 = Task(2, 5, FixedArrivalDistribution(5), displayName='t1')
    t2 = Task(4, 7, FixedArrivalDistribution(7), displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset,
                            time=35,
                            schedulingPolicy=RMSchedulingPolicy(),
                            deadlineMissFilter=True)
    run = SimulationRun(setup)
    result = run.result()
    deadlineMiss = result.history.firstDeadlineMiss()
    expectedMiss = DeadlineMiss(t2, 0)
    assert deadlineMiss == expectedMiss


def test_exactSameTask():
    t1 = Task(4, 2, FixedArrivalDistribution(2), displayName='t1', uniqueId=0)
    t2 = Task(4, 2, FixedArrivalDistribution(2), displayName='t2', uniqueId=1)
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=5)
    run = SimulationRun(setup)
    result = run.result()
    testTime = 2

    state = result.history[testTime]
    logging.debug('Effective %s', state)
    expected = SimulatorState(testTime,
                              [JobState(t2, 0),
                               JobState(t2, 1),
                               JobState(t2, 2),
                               JobState(t1, 0, progress=2, lastStart=2),
                               JobState(t1, 1),
                               JobState(t1, 2)],
                              [StateDeadline(4, t2, 1),
                               StateArrival(4, t2, 2),
                               StateArrival(4, t1, 2),
                               StateDeadline(4, t1, 1),
                               StateCompletion(4, t1, 0)],
                              deadlineMisses=[
                                  DeadlineMiss(t1, 0),
                                  DeadlineMiss(t2, 0)
                              ],
                              scheduler=EDFSchedulerState((2, t1, 0),
                                                          (2, 1, t2, 0),
                                                          (4, t1, 1),
                                                          (4, 1, t2, 1)))
    logging.debug('Expected  %s', expected)
    assert state == expected


def test_readyQueueCollision():
    t1 = Task(1, 2, FixedArrivalDistribution(3),
              displayName='t1')
    t2 = Task(4, 5, PoissonArrivalDistribution(6, 2), FixedPreemptionCost(3),
              displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=200)
    run = SimulationRun(setup)
    run.execute()


def test_readyQueueCollision2():
    t1 = Task(4, 2, FixedArrivalDistribution(2), displayName='t1')
    t2 = Task(5, 2, FixedArrivalDistribution(2), displayName='t2')
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset, time=5)
    run = SimulationRun(setup)
    run.execute()


def test_equalArrivals():
    t1 = Task(1, 4, FixedArrivalDistribution(4), displayName='t1')
    t2 = Task(1, 5, FixedArrivalDistribution(5), displayName='t2')
    taskset = Taskset(t1, t2)
    endTime = 22
    sim = Simulation(taskset)
    state = sim.getState(endTime)
    expected = SimulatorState(endTime,
                              [JobState(t2, 5),
                               JobState(t1, 5, 1, lastStart=21),
                               JobState(t1, 6),
                               JobState(t2, 4, 1, lastStart=22)],
                              [StateArrival(25, t2, 5),
                               StateDeadline(25, t2, 4),
                               StateCompletion(22, t2, 4),
                               StateDeadline(24, t1, 5),
                               StateArrival(24, t1, 6)],
                              scheduler=EDFSchedulerState((25, t2, 4)))
    assert(state == expected)


def test_simulateToDeadlineMiss():
    t1 = Task(20,
              50,
              FixedArrivalDistribution(50),
              displayName='t1')
    t2 = Task(2,
              3,
              FixedArrivalDistribution(3),
              displayName='t2')
    taskset = (t1, t2)
    sim = Simulation(taskset)
    state = sim.firstDeadlineMiss()
    expected = SimulatorState(50,
                              [JobState(t2, 16),
                               JobState(t1, 2),
                               JobState(t1, 0, 16, lastStart=48),
                               JobState(t1, 1),
                               JobState(t2, 17)],
                              [StateArrival(100, t1, 2),
                               StateDeadline(51, t2, 16),
                               StateCompletion(52, t1, 0),
                               StateArrival(51, t2, 17),
                               StateDeadline(100, t1, 1)],
                              deadlineMisses=[DeadlineMiss(t1, 0)],
                              scheduler=EDFSchedulerState((50, t1, 0),
                                                          (51, t2, 16),
                                                          (100, t1, 1)))
    assert(state == expected)


def test_preemptionMap():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    displayName='long')
    shortTask = Task(1,
                     5,
                     FixedArrivalDistribution(5),
                     displayName='short')

    taskset = Taskset(longTask, shortTask)
    sim = Simulation(taskset)
    endTime = 50

    expectedPreemptions = {
        Preemption(5, longTask, 0, shortTask, 1),
        Preemption(10, longTask, 0, shortTask, 2),
        Preemption(15, longTask, 0, shortTask, 3),
        Preemption(20, longTask, 0, shortTask, 4)}
    allPreemptions = sim.preemptions(endTime)
    assert(expectedPreemptions == allPreemptions)
    preemptionsByPreemptedTask = sim.preemptions(endTime,
                                                 preemptedTask=longTask)
    assert(expectedPreemptions == preemptionsByPreemptedTask)
    preemptionsByPreemptingTask = sim.preemptions(endTime,
                                                  preemptingTask=shortTask)
    assert(expectedPreemptions == preemptionsByPreemptingTask)

    expectedPreemptionsAtTime15 = {
        Preemption(15, longTask, 0, shortTask, 3)
    }
    preemptionsAtTime15 = sim.preemptions(endTime, time=15)
    assert(expectedPreemptionsAtTime15 == preemptionsAtTime15)

    expectedPreemptionsAtTime19 = set()
    preemptionsAtTime19 = sim.preemptions(endTime, time=19)
    assert(expectedPreemptionsAtTime19 == preemptionsAtTime19)


def test_preemptionInState():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    displayName='long')
    shortTask = Task(1,
                     9,
                     FixedArrivalDistribution(9),
                     displayName='short')
    taskset = Taskset(longTask, shortTask)
    sim = Simulation(taskset)
    preemptTime = 9
    endTime = 10
    sim.getState(endTime)
    state = sim.getState(preemptTime)
    expectedJobs = [JobState(longTask, 1),
                    JobState(longTask, 0, 8),
                    JobState(shortTask, 1, lastStart=9),
                    JobState(shortTask, 2)]
    expectedEvents = [StateDeadline(18, shortTask, 1),
                      StateDeadline(50, longTask, 0),
                      StateArrival(50, longTask, 1),
                      StateArrival(18, shortTask, 2),
                      StateCompletion(10, shortTask, 1),
                      StateCompletion(21, longTask, 0)]
    expectedPreemptions = [Preemption(9, longTask, 0, shortTask, 1)]
    expectedScheduler = EDFSchedulerState((18, shortTask, 1), (50, longTask, 0))
    expected = SimulatorState(preemptTime,
                              expectedJobs,
                              expectedEvents,
                              preemptions=expectedPreemptions,
                              scheduler=expectedScheduler)

    assert(state == expected)


def test_simuPreemptionCostOneTask():
    task = Task(2,
                3,
                FixedArrivalDistribution(6),
                FixedPreemptionCost(2),
                displayName='t')
    taskset = Taskset(task)
    sim = Simulation(taskset)
    endTime = 101
    state = sim.getState(endTime)
    expectedJobs = [JobState(task, 17)]
    expectedEvents = [StateArrival(102, task, 17)]
    expected = SimulatorState(endTime, expectedJobs, expectedEvents)

    assert(state == expected)


def test_simuLogPreemptionCostTwoTasks():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    LogPreemptionCost(0, 0.2),
                    displayName='long')
    shortTask = Task(1,
                     9,
                     FixedArrivalDistribution(9),
                     displayName='short')
    taskset = Taskset(longTask, shortTask)
    sim = Simulation(taskset)
    endTime = 50
    debtTime = 10

    state1 = sim.getState(debtTime)
    expectedJobs1 = [JobState(shortTask, 1, 1, lastStart=10),
                     JobState(shortTask, 2),
                     JobState(longTask, 1),
                     JobState(longTask, 0, 8, preemptionDebt=2)]
    expectedEvents1 = [StateDeadline(50, longTask, 0),
                       StateDeadline(18, shortTask, 1),
                       StateCompletion(10, shortTask, 1),
                       StateCompletion(21, longTask, 0),
                       StateArrival(18, shortTask, 2),
                       StateArrival(50, longTask, 1)]
    expectedScheduler1 = EDFSchedulerState((18, shortTask, 1),
                                           (50, longTask, 0))
    expected1 = SimulatorState(debtTime,
                               expectedJobs1,
                               expectedEvents1,
                               scheduler=expectedScheduler1)
    logging.debug(state1)
    logging.debug(expected1)
    assert(state1 == expected1)

    state2 = sim.getState(endTime)
    expectedJobs2 = [JobState(shortTask, 5, 1, lastStart=46),
                     JobState(shortTask, 6),
                     JobState(longTask, 0, 20, lastStart=27),
                     JobState(longTask, 1)]
    expectedEvents2 = [StateDeadline(50, longTask, 0),
                       StateArrival(54, shortTask, 6),
                       StateArrival(50, longTask, 1),
                       StateDeadline(54, shortTask, 5)]
    expected2 = SimulatorState(endTime,
                               expectedJobs2,
                               expectedEvents2)
    logging.debug(state2)
    assert(sim.noDeadlineMiss(endTime))
    assert(state2 == expected2)


def test_simuPreemptionCostTwoTasks():
    longTask = Task(20,
                    50,
                    FixedArrivalDistribution(50),
                    FixedPreemptionCost(2),
                    displayName='long')
    shortTask = Task(1,
                     9,
                     FixedArrivalDistribution(9),
                     displayName='short')
    taskset = Taskset(longTask, shortTask)
    sim = Simulation(taskset)
    endTime = 50
    debtTime = 10

    state1 = sim.getState(debtTime)
    expectedJobs1 = [JobState(shortTask, 1, 1, lastStart=10),
                     JobState(shortTask, 2),
                     JobState(longTask, 1),
                     JobState(longTask, 0, 8, preemptionDebt=2)]
    expectedEvents1 = [StateDeadline(50, longTask, 0),
                       StateDeadline(18, shortTask, 1),
                       StateCompletion(10, shortTask, 1),
                       StateCompletion(21, longTask, 0),
                       StateArrival(18, shortTask, 2),
                       StateArrival(50, longTask, 1)]
    expectedScheduler1 = EDFSchedulerState((18, shortTask, 1),
                                           (50, longTask, 0))
    expected1 = SimulatorState(debtTime,
                               expectedJobs1,
                               expectedEvents1,
                               scheduler=expectedScheduler1)
    assert(state1 == expected1)

    state2 = sim.getState(endTime)
    expectedJobs2 = [JobState(shortTask, 5, 1, lastStart=46),
                     JobState(shortTask, 6),
                     JobState(longTask, 0, 20, lastStart=27),
                     JobState(longTask, 1)]
    expectedEvents2 = [StateDeadline(50, longTask, 0),
                       StateArrival(54, shortTask, 6),
                       StateArrival(50, longTask, 1),
                       StateDeadline(54, shortTask, 5)]
    expected2 = SimulatorState(endTime,
                               expectedJobs2,
                               expectedEvents2)

    assert(sim.noDeadlineMiss(endTime))
    assert(state2 == expected2)


def test_createTaskWithLogPreemptionCost():
    task = Task(2, 3, FixedArrivalDistribution(6), LogPreemptionCost(0, 0.1))
    assert(task.wcet == 2)
    assert(task.deadline == 3)
    assert(task.arrivalDistribution == FixedArrivalDistribution(6))
    assert(task.preemptionCost == LogPreemptionCost(0, 0.1))


def test_createTaskWithPreemptionCost():
    task = Task(2, 3, FixedArrivalDistribution(6), FixedPreemptionCost(2))
    assert(task.wcet == 2)
    assert(task.deadline == 3)
    assert(task.arrivalDistribution == FixedArrivalDistribution(6))
    assert(task.preemptionCost == FixedPreemptionCost(2))


def test_simuOneTask():
    task = Task(2, 3, FixedArrivalDistribution(4), displayName='t')
    taskset = Taskset(task)
    sim = Simulation(taskset)
    endTime = 101
    state = sim.getState(endTime)
    expectedJobs = [JobState(task, 25, 1, lastStart=101),
                    JobState(task, 26)]
    expectedEvents = [StateCompletion(102, task, 25),
                      StateArrival(104, task, 26),
                      StateDeadline(103, task, 25)]
    expectedScheduler = EDFSchedulerState((103, task, 25))
    expected = SimulatorState(endTime,
                              expectedJobs,
                              expectedEvents,
                              scheduler=expectedScheduler)

    assert(state == expected)


def test_simuSporadicTask():
    t1 = Task(2, 3, PoissonArrivalDistribution(4, 3, 0), displayName='t')
    taskset = Taskset(t1)
    sim = Simulation(taskset)
    endTime = 77
    state = sim.getState(endTime)
    expectedJobs = [JobState(t1, 11),
                    JobState(t1, 10, 2, lastStart=76)]
    expectedEvents = [StateArrival(81, t1, 11),
                      StateDeadline(77, t1, 10)]
    expected = SimulatorState(endTime, expectedJobs, expectedEvents)
    assert(state == expected)
    assert(sim.noDeadlineMiss(endTime))


def test_deadlineMiss():
    task = Task(4, 3, FixedArrivalDistribution(5), displayName='t')
    taskset = Taskset(task)
    sim = Simulation(taskset)
    endTime = 5
    missTime = 3
    sim.getState(endTime)
    deadlineState = sim.getState(missTime)
    (deadlineMissFromState,) = deadlineState.deadlineMisses
    history = sim.history
    deadlineMissFromHistory, = history.deadlineMisses(endTime,
                                                      time=3,
                                                      task=task)

    expectedMiss = DeadlineMiss(task, 0)
    assert(deadlineMissFromState == expectedMiss)
    assert(deadlineMissFromHistory == expectedMiss)


def test_simuManyPreemptions():
    t1 = Task(1, 2, FixedArrivalDistribution(2), displayName='task1')
    t2 = Task(10, 20, FixedArrivalDistribution(20), displayName='task2')
    taskset = Taskset(t1, t2)
    sim = Simulation(taskset)
    endTime = 20
    state = sim.getState(endTime)

    logging.debug('%s', state)
    expectedJobs = [JobState(t1, 9, 1, lastStart=20),
                    JobState(t2, 0, 10, lastStart=19),
                    JobState(t1, 10),
                    JobState(t2, 1)]
    expectedEvents = [StateArrival(20, t1, 10),
                      StateArrival(20, t2, 1),
                      StateCompletion(20, t1, 9),
                      StateDeadline(20, t1, 9),
                      StateDeadline(20, t2, 0)]
    expectedScheduler = EDFSchedulerState((20, 1, t1, 9))
    expected = SimulatorState(endTime,
                              expectedJobs,
                              expectedEvents,
                              scheduler=expectedScheduler)
    assert(state == expected)
    assert(sim.noDeadlineMiss(endTime))


def test_simuManyPreemptionsFailing():
    t1 = Task(1, 2, FixedArrivalDistribution(2), displayName='task1')
    t2 = Task(11, 20, FixedArrivalDistribution(20), displayName='task2')
    taskset = Taskset(t1, t2)
    sim = Simulation(taskset)
    endTime = 21
    state = sim.getState(endTime)

    logging.debug('%s', state)
    expectedJobs = [JobState(t1, 9, 1, lastStart=21),
                    JobState(t1, 11),
                    JobState(t1, 10),
                    JobState(t2, 1),
                    JobState(t2, 2)]
    expectedEvents = [StateArrival(22, t1, 11),
                      StateArrival(40, t2, 2),
                      StateCompletion(21, t1, 9),
                      StateDeadline(22, t1, 10),
                      StateDeadline(40, t2, 1)]
    expectedScheduler = EDFSchedulerState((20, 1, t1, 9),
                                          (22, t1, 10),
                                          (40, t2, 1))
    expected = SimulatorState(endTime,
                              expectedJobs,
                              expectedEvents,
                              scheduler=expectedScheduler)
    assert(state == expected)
    expectedDeadlineMisses = {DeadlineMiss(t1, 9)}
    assert(sim.deadlineMisses(endTime) == expectedDeadlineMisses)


def test_simuTwoTasks():
    t1 = Task(2, 3, FixedArrivalDistribution(4), displayName='t1')
    t2 = Task(1, 4, FixedArrivalDistribution(5), displayName='t2')
    taskset = Taskset(t1, t2)
    sim = Simulation(taskset)
    endTime = 77
    state = sim.getState(endTime)

    expectedJobs = [JobState(t1, 19, 1, lastStart=77),
                    JobState(t2, 15, 1, lastStart=76),
                    JobState(t2, 16),
                    JobState(t1, 20)]
    expectedEvents = [StateArrival(80, t2, 16),
                      StateArrival(80, t1, 20),
                      StateCompletion(78, t1, 19),
                      StateDeadline(79, t2, 15),
                      StateDeadline(79, t1, 19)]
    expectedScheduler = EDFSchedulerState((79, t1, 19))
    expected = SimulatorState(endTime,
                              expectedJobs,
                              expectedEvents,
                              scheduler=expectedScheduler)

    logging.debug('%s', state)
    assert(state == expected)


def test_simuAndResumeOneTask1():
    t1 = Task(2, 3, FixedArrivalDistribution(4), displayName='t')
    taskset = Taskset(t1)
    sim = Simulation(taskset)
    time1 = 7
    time2 = 13
    state1 = sim.getState(time1)

    expectedJobs1 = [JobState(t1, 2),
                     JobState(t1, 1, 2, lastStart=6)]
    expectedEvents1 = [StateArrival(8, t1, 2), StateDeadline(7, t1, 1)]
    expected1 = SimulatorState(time1, expectedJobs1, expectedEvents1)

    assert(expected1 == state1)

    state2 = sim.getState(time2)

    expectedJobs2 = [JobState(t1, 3, 1, lastStart=13),
                     JobState(t1, 4)]
    expectedEvents2 = [StateCompletion(14, t1, 3),
                       StateArrival(16, t1, 4),
                       StateDeadline(15, t1, 3)]
    expectedScheduler2 = EDFSchedulerState((15, t1, 3))
    expected2 = SimulatorState(time2,
                               expectedJobs2,
                               expectedEvents2,
                               scheduler=expectedScheduler2)

    assert(expected2 == state2)


def test_simuAndResumeOneTask2():
    t1 = Task(2, 3, FixedArrivalDistribution(4), displayName='t')
    taskset = Taskset(t1)
    sim = Simulation(taskset)
    time1 = 6
    time2 = 13
    state1 = sim.getState(time1)

    expectedJobs1 = [JobState(t1, 1, 2, lastStart=6),
                     JobState(t1, 2)]
    expectedEvents1 = [StateCompletion(6, t1, 1),
                       StateArrival(8, t1, 2),
                       StateDeadline(7, t1, 1)]
    expectedScheduler1 = EDFSchedulerState((7, t1, 1))
    expected1 = SimulatorState(
        time1, expectedJobs1, expectedEvents1, scheduler=expectedScheduler1)

    assert(expected1 == state1)

    state2 = sim.getState(time2)

    expectedJobs2 = [JobState(t1, 3, 1, lastStart=13), JobState(t1, 4)]
    expectedEvents2 = [StateCompletion(14, t1, 3),
                       StateArrival(16, t1, 4),
                       StateDeadline(15, t1, 3)]
    expectedScheduler2 = EDFSchedulerState((15, t1, 3))
    expected2 = SimulatorState(
        time2, expectedJobs2, expectedEvents2, scheduler=expectedScheduler2)

    assert(expected2 == state2)


def test_simuAndResumeShort():
    t1 = Task(2, 3, FixedArrivalDistribution(4), displayName='t1')
    t2 = Task(1, 4, FixedArrivalDistribution(5), displayName='t2')
    taskset = Taskset(t1, t2)
    sim = Simulation(taskset)
    time1 = 6
    time2 = 13
    state1 = sim.getState(time1)

    expectedJobs1 = [JobState(t1, 1, 2, lastStart=6),
                     JobState(t1, 2),
                     JobState(t2, 1),
                     JobState(t2, 2)]
    expectedEvents1 = [StateCompletion(6, t1, 1),
                       StateArrival(8, t1, 2),
                       StateArrival(10, t2, 2),
                       StateDeadline(9, t2, 1),
                       StateDeadline(7, t1, 1)]
    expectedScheduler1 = EDFSchedulerState((7, t1, 1), (9, t2, 1))
    expected1 = SimulatorState(
        time1, expectedJobs1, expectedEvents1, scheduler=expectedScheduler1)

    logging.debug('%s', state1)
    assert(expected1 == state1)

    state2 = sim.getState(time2)

    expectedJobs2 = [JobState(t1, 3, 1, lastStart=13),
                     JobState(t2, 2, 1, lastStart=11),
                     JobState(t1, 4),
                     JobState(t2, 3)]
    expectedEvents2 = [StateCompletion(14, t1, 3),
                       StateArrival(16, t1, 4),
                       StateArrival(15, t2, 3),
                       StateDeadline(15, t1, 3),
                       StateDeadline(14, t2, 2)]
    expectedScheduler2 = EDFSchedulerState((15, t1, 3))
    expected2 = SimulatorState(
        time2, expectedJobs2, expectedEvents2, scheduler=expectedScheduler2)

    logging.debug('%s', state2)
    assert(expected2 == state2)

    assert(sim.noDeadlineMiss(time2))


def test_simuAndResumeLong():
    t1 = Task(2, 3, FixedArrivalDistribution(4), displayName='t1')
    t2 = Task(1, 4, FixedArrivalDistribution(5), displayName='t2')
    taskset = Taskset(t1, t2)
    sim = Simulation(taskset)
    time1 = 77
    time2 = 113
    state77 = sim.getState(time1)

    expectedJobs77 = [JobState(t1, 19, 1, lastStart=77),
                      JobState(t2, 15, 1, lastStart=76),
                      JobState(t2, 16),
                      JobState(t1, 20)]
    expectedEvents77 = [StateArrival(80, t2, 16),
                        StateArrival(80, t1, 20),
                        StateCompletion(78, t1, 19),
                        StateDeadline(79, t1, 19),
                        StateDeadline(79, t2, 15)]
    expectedScheduler1 = EDFSchedulerState((79, t1, 19))
    expected77 = SimulatorState(time1,
                                expectedJobs77,
                                expectedEvents77,
                                scheduler=expectedScheduler1)

    assert(expected77 == state77)

    state113 = sim.getState(time2)
    expectedJobs113 = [JobState(t2, 23),
                       JobState(t1, 28, 1, lastStart=113),
                       JobState(t2, 22, 1, lastStart=111),
                       JobState(t1, 29)]
    expectedEvents113 = [StateArrival(116, t1, 29),
                         StateCompletion(114, t1, 28),
                         StateArrival(115, t2, 23),
                         StateDeadline(115, t1, 28),
                         StateDeadline(114, t2, 22)]
    expectedScheduler2 = EDFSchedulerState((115, t1, 28))
    expected113 = SimulatorState(time2,
                                 expectedJobs113,
                                 expectedEvents113,
                                 scheduler=expectedScheduler2)

    assert(sim.noDeadlineMiss(time2))
    assert(expected113 == state113)
