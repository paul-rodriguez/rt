
import pytest

from crpd.model import Task, Taskset
from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationRun, SimulationSetup
from crpd.hist import DeadlineMiss
from crpd.gen import TasksetGenerator, RandomValue, PeriodGenerator
from dualpriority.burns import burnsWellingsPolicy
from dualpriority.policies import (rmLaxityPromotions,
                                   dichotomicPromotionSearch,
                                   dajamPromotions,
                                   genLpViableTasks,
                                   greedyDeadlineFixPolicy)
from dualpriority.threeTasks import (RMWorstCaseLaxity3TaskOptimiser,
                                     FixedPointThreeTaskOptimiser,
                                     OptimisationFailure)


def test_GDF_3tasks():
    taskset = Taskset(Task(21, 40),
                      Task(1, 58),
                      Task(25, 57))

    policy = greedyDeadlineFixPolicy(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


@pytest.mark.skip
def test_GDF_4tasks():
    taskset = Taskset(Task(1, 40),
                      Task(12, 101),
                      Task(16, 48),
                      Task(37, 73))

    policy = greedyDeadlineFixPolicy(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


@pytest.mark.skip
def test_GDF_5tasks():
    taskset = Taskset(Task(1, 40),
                      Task(9, 107),
                      Task(1, 54),
                      Task(43, 60),
                      Task(7, 51))
    policy = greedyDeadlineFixPolicy(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


@pytest.mark.skip
def test_GDF_bulk():
    systems = (Taskset(Task(1, 40),
                       Task(17, 119),
                       Task(7, 60),
                       Task(35, 100),
                       Task(27, 75)),
               Taskset(Task(1, 40),
                       Task(16, 92),
                       Task(27, 75),
                       Task(17, 55),
                       Task(6, 50)),
               Taskset(Task(1, 40),
                       Task(16, 112),
                       Task(7, 60),
                       Task(35, 100),
                       Task(27, 75)),
               Taskset(Task(9, 40),
                       Task(9, 74),
                       Task(35, 54)),
               Taskset(Task(1, 40),
                       Task(17, 106),
                       Task(29, 62),
                       Task(33, 96)),
               Taskset(Task(1, 40),
                       Task(16, 91),
                       Task(27, 75),
                       Task(17, 55),
                       Task(6, 50)),
               Taskset(Task(11, 40),
                       Task(14, 82),
                       Task(31, 58)))

    for taskset in systems:
        policy = greedyDeadlineFixPolicy(taskset)
        setup = SimulationSetup(taskset,
                                taskset.hyperperiod,
                                schedulingPolicy=policy,
                                deadlineMissFilter=True)
        result = SimulationRun(setup).result()
        history = result.history
        assert not history.hasDeadlineMiss()


def test_lpvTrivial1():
    t1 = Task(1, 10)
    t2 = Task(2, 30)
    t3 = Task(5, 100)
    taskset = Taskset(t1, t2, t3)
    expected = {t1, t2, t3}
    lpvTasks = set(genLpViableTasks(taskset))
    assert lpvTasks == expected


def test_lpvTrivial2():
    taskset = Taskset(Task(13536, 67999),
                      Task(1440, 90690),
                      Task(2266, 39305),
                      Task(2512, 28902),
                      Task(3374, 62477),
                      Task(377, 20593))
    expected = set(taskset)
    lpvTasks = set(genLpViableTasks(taskset))
    assert lpvTasks == expected


def test_lpvTrivialGen():
    pg = PeriodGenerator(randomValue=RandomValue(logRange=(10, 100)))
    gen = TasksetGenerator(seed=1337,
                           utilization=RandomValue(floatrange=(0.1, 0.65)),
                           periodGenerator=pg,
                           nbTasks=RandomValue(intrange=(2, 10)))
    for _ in range(100):
        taskset = gen()
        lpvTasks = set(genLpViableTasks(taskset))
        expected = set(taskset)
        assert lpvTasks == expected


def test_lpvNonTrivial():
    t4 = Task(587, 45124)
    taskset = Taskset(Task(1155, 15964),
                      Task(1649, 10359),
                      Task(4343, 14821),
                      t4,
                      Task(6028, 19430))
    expected = {t4}
    lpvTasks = set(genLpViableTasks(taskset))
    assert lpvTasks == expected


def test_lpvSearch():
    taskset = Taskset(Task(10, 24), Task(31, 83), Task(12, 90))
    expected = set(taskset)
    lpvTasks = set(genLpViableTasks(taskset))
    assert lpvTasks == expected


def test_noPreprocessingFailures():
    systems = (Taskset(Task(1, 40),
                       Task(17, 119),
                       Task(7, 60),
                       Task(35, 100),
                       Task(27, 75)),
               Taskset(Task(1, 40),
                       Task(16, 92),
                       Task(27, 75),
                       Task(17, 55),
                       Task(6, 50)),
               Taskset(Task(1, 40),
                       Task(16, 112),
                       Task(7, 60),
                       Task(35, 100),
                       Task(27, 75)),
               Taskset(Task(1, 40),
                       Task(12, 101),
                       Task(16, 48),
                       Task(37, 73)),
               Taskset(Task(9, 40),
                       Task(9, 74),
                       Task(35, 54)),
               Taskset(Task(1, 40),
                       Task(17, 106),
                       Task(29, 62),
                       Task(33, 96)),
               Taskset(Task(1, 40),
                       Task(16, 91),
                       Task(27, 75),
                       Task(17, 55),
                       Task(6, 50)),
               Taskset(Task(11, 40),
                       Task(14, 82),
                       Task(31, 58)),
               Taskset(Task(1, 40),
                       Task(9, 107),
                       Task(1, 54),
                       Task(43, 60),
                       Task(7, 51)),
               Taskset(Task(21, 40),
                       Task(1, 58),
                       Task(25, 57)))

    for taskset in systems:
        lpvTasks = set(genLpViableTasks(taskset))
        assert not lpvTasks
        policy = rmLaxityPromotions(taskset)
        setup = SimulationSetup(taskset,
                                taskset.hyperperiod,
                                schedulingPolicy=policy,
                                deadlineMissFilter=True)
        result = SimulationRun(setup).result()
        history = result.history
        assert history.hasDeadlineMiss()


def test_noPrepFailure1():
    taskset = Taskset(Task(7, 24),
                      Task(4, 50),
                      Task(22, 36))

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert history.hasDeadlineMiss()


def test_withPrepFailure1():
    taskset = Taskset(Task(1, 24),
                      Task(12, 127),
                      Task(11, 26),
                      Task(1, 100),
                      Task(16, 39))
    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True)
    result = SimulationRun(setup).result()
    history = result.history
    assert history.hasDeadlineMiss()


def test_dajamPromo1():
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)
    taskset = Taskset(t1, t2, t3)

    policy = dajamPromotions(taskset)

    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    history = SimulationRun(setup).result().history
    assert not history.hasDeadlineMiss()


@pytest.mark.skip
def test_bwPolicy1():
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)
    taskset = Taskset(t1, t2, t3)

    bwPolicy = burnsWellingsPolicy(taskset)

    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=bwPolicy,
                            trackHistory=True,
                            trackPreemptions=False)
    history = SimulationRun(setup).result().history
    assert not history.hasDeadlineMiss()


def test_counterExample1():
    t1 = Task(23, 40)
    t2 = Task(23, 58)
    t3 = Task(1, 60)
    taskset = Taskset(t1, t2, t3)

    rmlPolicy = rmLaxityPromotions(taskset)
    rmlSetup = SimulationSetup(taskset,
                               taskset.hyperperiod,
                               schedulingPolicy=rmlPolicy,
                               trackHistory=True,
                               trackPreemptions=False)
    rmlHistory = SimulationRun(rmlSetup).result().history
    assert rmlHistory.hasDeadlineMiss()

    dPolicy = dichotomicPromotionSearch(taskset)
    dSetup = SimulationSetup(taskset,
                             taskset.hyperperiod,
                             schedulingPolicy=dPolicy,
                             trackHistory=True,
                             trackPreemptions=False)
    dHistory = SimulationRun(dSetup).result().history
    assert not dHistory.hasDeadlineMiss()


def test_example1():
    t1 = Task(38, 51)
    t2 = Task(1, 52)
    t3 = Task(8, 42)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_example2():
    t1 = Task(5, 18)
    t2 = Task(16, 24)
    t3 = Task(1, 25)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_example3():
    t1 = Task(3, 6)
    t2 = Task(4, 9)
    t3 = Task(1, 18)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_example4():
    t1 = Task(6, 13)
    t2 = Task(8, 18)
    t3 = Task(6, 86)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert history.hasDeadlineMiss()


def test_example5():
    t1 = Task(13, 51)
    t2 = Task(83, 128)
    t3 = Task(16, 183)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert history.hasDeadlineMiss()


@pytest.mark.slowtest
def test_example5AnyPromo():
    t1 = Task(13, 51)
    t2 = Task(83, 128)
    t3 = Task(16, 183)
    taskset = Taskset(t1, t2, t3)

    policy = dichotomicPromotionSearch(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_example6():
    t1 = Task(22, 87)
    t2 = Task(131, 237)
    t3 = Task(53, 280)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert history.hasDeadlineMiss()


def test_example7():
    t1 = Task(1, 5)
    t2 = Task(6, 39)
    t3 = Task(16, 39)
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_damien1():
    t1 = Task(1, 4, displayName='t1')
    t2 = Task(2, 15, displayName='t2')
    t3 = Task(14, 23, displayName='t3')
    t4 = Task(1, 1380, displayName='t4')
    taskset = Taskset(t1, t2, t3, t4)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_damien2():
    t1 = Task(3, 6, displayName='t1')
    t2 = Task(4, 9, displayName='t2')
    t3 = Task(2, 36, displayName='t3')
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


@pytest.mark.skip
def test_damien3():
    t1 = Task(8, 20, displayName='t1')
    t2 = Task(15, 28, displayName='t2')
    t3 = Task(8, 136, displayName='t3')
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


@pytest.mark.skip
def test_damien4():
    t1 = Task(8, 20, displayName='t1')
    t2 = Task(15, 28, displayName='t2')
    t3 = Task(8, 136, displayName='t3')
    taskset = Taskset(t1, t2, t3)

    policy = dichotomicPromotionSearch(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_laurent1():
    t1 = Task(2, 11, displayName='t1')
    t2 = Task(9, 19, displayName='t2')
    t3 = Task(7, 21, displayName='t3')
    taskset = Taskset(t1, t2, t3)

    policy = rmLaxityPromotions(taskset)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=True,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_3PWorstLaxity1():
    taskset = Taskset(Task(33, 90),
                      Task(16, 39),
                      Task(3, 28))
    optimiser = RMWorstCaseLaxity3TaskOptimiser(taskset)
    history = optimiser.history()
    assert not history.hasDeadlineMiss()


def test_firstT2Job1Standard():
    t1 = Task(2, 12, displayName='t1')
    t2 = Task(17, 33, displayName='t2')
    t3 = Task(13, 57, displayName='t3')
    taskset = Taskset(t1, t2, t3)

    policy = DualPrioritySchedulingPolicy(
        (t1, DualPriorityTaskInfo(3, 10, -3)),
        (t2, DualPriorityTaskInfo(2, 14, -2)),
        (t3, DualPriorityTaskInfo(1)))
    setup = SimulationSetup(taskset,
                            time=taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True)
    result = SimulationRun(setup).result()


def test_3Pworst():
    t1 = Task(3, 9)
    t2 = Task(8, 12)
    t3 = Task(1, 1000)

    taskset = Taskset(t1, t2, t3)
    optimisationFailed = False
    try:
        history = FixedPointThreeTaskOptimiser(taskset).history()
    except OptimisationFailure:
        optimisationFailed = True
    assert optimisationFailed


def test_3Psimple():
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)

    taskset = Taskset(t1, t2, t3)
    history = FixedPointThreeTaskOptimiser(taskset).history()
    assert not history.hasDeadlineMiss()


def test_3PMiss1():
    t1 = Task(5, 20)
    t2 = Task(64, 98)
    t3 = Task(1, 16)

    taskset = Taskset(t1, t2, t3)
    history = FixedPointThreeTaskOptimiser(taskset).history()
    assert not history.hasDeadlineMiss()


def test_analysisBW1():
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)

    taskset = Taskset(t1, t2, t3)
    policy = dichotomicPromotionSearch(taskset)

    expectedPolicy = DualPrioritySchedulingPolicy(
        (t1, DualPriorityTaskInfo(3, 3, -3)),
        (t2, DualPriorityTaskInfo(2, 6, -2)),
        (t3, DualPriorityTaskInfo(1)))
    assert expectedPolicy == policy


def test_analysisBW2():
    t1 = Task(3, 12)
    t2 = Task(4, 16)
    t3 = Task(4, 20)
    t4 = Task(6, 20)

    taskset = Taskset(t1, t2, t3, t4)
    policy = dichotomicPromotionSearch(taskset)

    expectedPolicy = DualPrioritySchedulingPolicy(
        (t1, DualPriorityTaskInfo(4, 9, -4)),
        (t2, DualPriorityTaskInfo(3, 9, -3)),
        (t3, DualPriorityTaskInfo(2)),
        (t4, DualPriorityTaskInfo(1)))
    assert expectedPolicy == policy


def test_analysisBW3():
    t1 = Task(4, 16)
    t2 = Task(5, 20)
    t3 = Task(11, 28)
    t4 = Task(6, 56)

    taskset = Taskset(t1, t2, t3, t4)
    policy = dichotomicPromotionSearch(taskset)

    expectedPolicy = DualPrioritySchedulingPolicy(
        (t1, DualPriorityTaskInfo(4, 12, -4)),
        (t2, DualPriorityTaskInfo(3, 11, -3)),
        (t3, DualPriorityTaskInfo(2, 8, -2)),
        (t4, DualPriorityTaskInfo(1)))
    assert policy == expectedPolicy


def test_analysisBW4():
    t1 = Task(1, 4)
    t2 = Task(1, 6)
    t3 = Task(3, 12)
    t4 = Task(5, 30)
    t5 = Task(6, 36)

    taskset = Taskset(t1, t2, t3, t4, t5)
    policy = dichotomicPromotionSearch(taskset)

    expectedPolicy = DualPrioritySchedulingPolicy(
        (t1, DualPriorityTaskInfo(5, 3, -5)),
        (t2, DualPriorityTaskInfo(4, 4, -4)),
        (t3, DualPriorityTaskInfo(3, 6, -3)),
        (t4, DualPriorityTaskInfo(2, 18, -2)),
        (t5, DualPriorityTaskInfo(1)))
    assert policy == expectedPolicy


def test_dualPriorityBW1_1():
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(2)),
                                          (t2, DualPriorityTaskInfo(3)),
                                          (t3, DualPriorityTaskInfo(4)))

    taskset = Taskset(t1, t2, t3)
    hyperperiod = 24
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    run = SimulationRun(setup)
    result = run.result()
    expectedMisses = {DeadlineMiss(t3, 0)}
    assert result.history.deadlineMisses(hyperperiod) == expectedMisses


def test_dualPriorityBW1_2():
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(1)),
                                          (t2, DualPriorityTaskInfo(3)),
                                          (t3, DualPriorityTaskInfo(4, 10, 2)))
    taskset = Taskset(t1, t2, t3)
    hyperperiod = 24
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    run = SimulationRun(setup)
    result = run.result()
    assert not result.history.hasDeadlineMiss()


def test_dualPriorityBW2_1():
    t1 = Task(3, 12)
    t2 = Task(4, 16)
    t3 = Task(4, 20)
    t4 = Task(6, 20)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6)),
                                          (t4, DualPriorityTaskInfo(7)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 240
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t4, 0)
    assert result.history.firstDeadlineMiss() == expectedMiss


def test_dualPriorityBW2_2():
    t1 = Task(3, 12)
    t2 = Task(4, 16)
    t3 = Task(4, 20)
    t4 = Task(6, 20)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(3)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6)),
                                          (t4, DualPriorityTaskInfo(7, 16, 4)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 240
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t4, 1)
    assert result.history.firstDeadlineMiss() == expectedMiss


def test_dualPriorityBW2_3():
    t1 = Task(3, 12)
    t2 = Task(4, 16)
    t3 = Task(4, 20)
    t4 = Task(6, 20)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6)),
                                          (t4, DualPriorityTaskInfo(7, 14, 3)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 240
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t3, 6)
    assert result.history.firstDeadlineMiss() == expectedMiss


def test_dualPriorityBW2_4():
    t1 = Task(3, 12)
    t2 = Task(4, 16)
    t3 = Task(4, 20)
    t4 = Task(6, 20)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6, 13, 3)),
                                          (t4, DualPriorityTaskInfo(7, 14, 2)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 240
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    assert not result.history.hasDeadlineMiss()


def test_dualPriorityBW3_1():
    t1 = Task(4, 16)
    t2 = Task(5, 20)
    t3 = Task(11, 28)
    t4 = Task(6, 56)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6)),
                                          (t4, DualPriorityTaskInfo(7)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 560
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t3, 0)
    assert result.history.firstDeadlineMiss() == expectedMiss


def test_dualPriorityBW3_2():
    t1 = Task(4, 16)
    t2 = Task(5, 20)
    t3 = Task(11, 28)
    t4 = Task(6, 56)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6, 19, 2)),
                                          (t4, DualPriorityTaskInfo(7, 50, 1)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 560
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t2, 16)
    actualMiss = result.history.firstDeadlineMiss()
    assert actualMiss == expectedMiss


def test_dualPriorityBW3_3():
    t1 = Task(4, 16)
    t2 = Task(5, 20)
    t3 = Task(11, 28)
    t4 = Task(6, 56)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5, 19, 3)),
                                          (t3, DualPriorityTaskInfo(6, 19, 2)),
                                          (t4, DualPriorityTaskInfo(7, 50, 1)))
    taskset = Taskset(t1, t2, t3, t4)
    hyperperiod = 560
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    assert not result.history.hasDeadlineMiss()


def test_dualPriorityBW4_1():
    t1 = Task(1, 4)
    t2 = Task(1, 6)
    t3 = Task(3, 12)
    t4 = Task(5, 30)
    t5 = Task(6, 36)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6)),
                                          (t4, DualPriorityTaskInfo(7)),
                                          (t5, DualPriorityTaskInfo(8)))
    taskset = Taskset(t1, t2, t3, t4, t5)
    hyperperiod = 180
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t5, 0)
    assert result.history.firstDeadlineMiss() == expectedMiss


def test_dualPriorityBW4_2():
    t1 = Task(1, 4)
    t2 = Task(1, 6)
    t3 = Task(3, 12)
    t4 = Task(5, 30)
    t5 = Task(6, 36)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(3)),
                                          (t2, DualPriorityTaskInfo(4)),
                                          (t3, DualPriorityTaskInfo(5)),
                                          (t4, DualPriorityTaskInfo(7)),
                                          (t5, DualPriorityTaskInfo(8, 23, 6)))
    taskset = Taskset(t1, t2, t3, t4, t5)
    hyperperiod = 180
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    expectedMiss = DeadlineMiss(t4, 4)
    assert result.history.firstDeadlineMiss() == expectedMiss


def test_dualPriorityBW4_3():
    t1 = Task(1, 4)
    t2 = Task(1, 6)
    t3 = Task(3, 12)
    t4 = Task(5, 30)
    t5 = Task(6, 36)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(4)),
                                          (t2, DualPriorityTaskInfo(5)),
                                          (t3, DualPriorityTaskInfo(6)),
                                          (t4, DualPriorityTaskInfo(7, 29, 4)),
                                          (t5, DualPriorityTaskInfo(8, 23, 6)))
    taskset = Taskset(t1, t2, t3, t4, t5)
    hyperperiod = 180
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    assert not result.history.hasDeadlineMiss()


def test_simuDualPrio():
    t1 = Task(5, 10)
    t2 = Task(10, 20)

    policy = DualPrioritySchedulingPolicy((t1, DualPriorityTaskInfo(11, 5, 1)),
                                          (t2, DualPriorityTaskInfo(12, 10, 2)))
    taskset = Taskset(t1, t2)
    setup = SimulationSetup(taskset,
                            time=40,
                            schedulingPolicy=policy)
    run = SimulationRun(setup)
    run.execute()
