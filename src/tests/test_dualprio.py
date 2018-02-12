
from .loggers import testLog, schedLog, simulatorLog, analysisLog
from crpd.model import Task, Taskset
from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationRun, SimulationSetup
from crpd.hist import DeadlineMiss
from dualpriority.burns import burnsWellingsPolicy
from dualpriority.policies import (rmLaxityPromotions,
                                   dichotomicPromotionSearch,
                                   dajamPromotions,
                                   genLpViableTasks)
from dualpriority.threeTasks import (RMWorstCaseLaxity3TaskOptimiser,
                                     FixedPointThreeTaskOptimiser,
                                     OptimisationFailure)


def test_lpvSearch(testLog):
    t2 = Task(11, 90)
    t3 = Task(31, 83)

    taskset = Taskset(Task(10, 24), t2, t3)

    expected = set([t2, t3])
    lpvTasks = set(genLpViableTasks(taskset))
    assert lpvTasks == expected


def test_noPrepFailure1(testLog):
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


def test_noPreprocessingFailures(testLog):
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
        lpvTasks = list(genLpViableTasks(taskset))
        assert not lpvTasks


def test_dajamPromo1(testLog):
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)
    taskset = Taskset(t1, t2, t3)

    policy = dajamPromotions(taskset)
    testLog.info('%s', policy)

    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    history = SimulationRun(setup).result().history
    assert not history.hasDeadlineMiss()


def test_bwPolicy1(testLog):
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)
    taskset = Taskset(t1, t2, t3)

    bwPolicy = burnsWellingsPolicy(taskset)
    testLog.info('%s', bwPolicy)

    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=bwPolicy,
                            trackHistory=True,
                            trackPreemptions=False)
    history = SimulationRun(setup).result().history
    assert not history.hasDeadlineMiss()


def test_counterExample1(testLog):
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


def test_example1(testLog):
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


def test_example2(testLog):
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


def test_example3(testLog):
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


def test_example4(testLog):
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


def test_example5(testLog):
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


def test_example5AnyPromo(testLog):
    t1 = Task(13, 51)
    t2 = Task(83, 128)
    t3 = Task(16, 183)
    taskset = Taskset(t1, t2, t3)

    policy = dichotomicPromotionSearch(taskset)
    testLog.info('Policy %s', policy)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    assert not history.hasDeadlineMiss()


def test_example6(testLog):
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


def test_example7(testLog):
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


def test_damien1(testLog):
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


def test_damien2(testLog):
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


def test_damien3(testLog):
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


def test_damien4(testLog):
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


def test_laurent1(testLog):
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


def test_3PWorstLaxity1(testLog):
    taskset = Taskset(Task(33, 90),
                      Task(16, 39),
                      Task(3, 28))
    optimiser = RMWorstCaseLaxity3TaskOptimiser(taskset)
    history = optimiser.history()
    assert not history.hasDeadlineMiss()


def test_firstT2Job1Standard(schedLog, simulatorLog):
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


def test_3Pworst(testLog):
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


def test_analysisBW1(analysisLog, testLog):
    t1 = Task(3, 6)
    t2 = Task(2, 8)
    t3 = Task(3, 12)

    taskset = Taskset(t1, t2, t3)
    policy = dichotomicPromotionSearch(taskset)

    expectedPolicy = DualPrioritySchedulingPolicy(
        (t1, DualPriorityTaskInfo(3, 3, -3)),
        (t2, DualPriorityTaskInfo(2, 6, -2)),
        (t3, DualPriorityTaskInfo(1)))
    testLog.info('Expected %s', expectedPolicy)
    testLog.info('Effective %s', policy)
    assert expectedPolicy == policy


def test_analysisBW2(analysisLog, testLog):
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
    testLog.info('Expected %s', expectedPolicy)
    testLog.info('Effective %s', policy)
    assert expectedPolicy == policy


def test_analysisBW3(analysisLog, testLog):
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
    testLog.info('Expected %s', expectedPolicy)
    testLog.info('Effective %s', policy)
    assert policy == expectedPolicy


def test_analysisBW4(analysisLog, testLog):
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
    testLog.info('Expected %s', expectedPolicy)
    testLog.info('Effective %s', policy)
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


def test_simuDualPrio(schedLog, simulatorLog):
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
