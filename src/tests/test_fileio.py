import os
import contextlib

from dualpriority.fileio import DPInputFile, DPOutputFile
from dualpriority.policies import rmLaxityPromotions
from crpd.model import Taskset, Task
from crpd.sim import SimulationSetup
from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo


def rmlSetups(*tasksets):
    for taskset in tasksets:
        policy = rmLaxityPromotions(taskset)
        setup = SimulationSetup(taskset,
                                taskset.hyperperiod,
                                schedulingPolicy=policy)
        yield setup


def cleanFile(path):
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)


def test_fileInput():
    Task.resetIdCounter()
    sif = DPInputFile('${HOME}/git/rt/tasksets/test.txt')
    setups = sif.lazyRead()
    setup1 = next(setups)
    t11 = Task(1, 5, uniqueId=0)
    t12 = Task(1, 3, uniqueId=1)
    taskset1 = Taskset(t11, t12)
    policy1 = DualPrioritySchedulingPolicy(
          (t11, DualPriorityTaskInfo(2)),
          (t12, DualPriorityTaskInfo(1)))
    expected1 = SimulationSetup(taskset1,
                                taskset1.hyperperiod,
                                schedulingPolicy=policy1)
    assert setup1 == expected1

    setup2 = next(setups)
    t21 = Task(2, 12, uniqueId=2)
    t22 = Task(17, 33, uniqueId=3)
    t23 = Task(13, 57, uniqueId=4)
    taskset2 = Taskset(t21, t22, t23)
    policy2 = DualPrioritySchedulingPolicy(
          (t21, DualPriorityTaskInfo(3, 10, -3)),
          (t22, DualPriorityTaskInfo(2, 14, -2)),
          (t23, DualPriorityTaskInfo(1)))
    expected2 = SimulationSetup(taskset2,
                                taskset2.hyperperiod,
                                schedulingPolicy=policy2)
    assert setup2 == expected2

    setup3 = next(setups)
    t31 = Task(3, 12, uniqueId=5)
    t32 = Task(4, 16, uniqueId=6)
    t33 = Task(4, 20, uniqueId=7)
    t34 = Task(6, 20, uniqueId=8)
    taskset3 = Taskset(t31, t32, t33, t34)
    policy3 = DualPrioritySchedulingPolicy(
          (t31, DualPriorityTaskInfo(4, 12, -4)),
          (t32, DualPriorityTaskInfo(3, 9, -3)),
          (t33, DualPriorityTaskInfo(2)),
          (t34, DualPriorityTaskInfo(1)))
    expected3 = SimulationSetup(taskset3,
                                taskset3.hyperperiod,
                                schedulingPolicy=policy3)
    assert setup3 == expected3


def test_fileOutputNoPromo():
    taskset = Taskset(Task(1, 40),
                      Task(4, 42),
                      Task(1, 46),
                      Task(10, 46),
                      Task(28, 60),
                      Task(11, 64))

    def dpInfos():
        sortedTasks = sorted(taskset,
                             key=lambda x: (x.minimalInterArrivalTime, x.wcet))
        for i, task in enumerate(sortedTasks):
            yield task, DualPriorityTaskInfo(i + 1)
    policy = DualPrioritySchedulingPolicy(*dpInfos())
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy)
    testPath = 'test_fileOutputNoPromo.txt'
    sof = DPOutputFile(testPath)
    cleanFile(testPath)
    sof.write(setup)

    expectedFileContent = ('1 40 40 40 1 1\n'
                           '4 42 42 42 2 2\n'
                           '1 46 46 46 3 3\n'
                           '10 46 46 46 4 4\n'
                           '28 60 60 60 5 5\n'
                           '11 64 64 64 6 6\n'
                           '\n')
    with open(testPath) as file:
        fileContent = file.read()
        assert fileContent == expectedFileContent
    cleanFile(testPath)


def test_fileOutput2Setups():
    tasksets = (Taskset(Task(1, 40),
                        Task(11, 46),
                        Task(35, 56),
                        Task(10, 99)),
                Taskset(Task(14, 40),
                        Task(36, 69),
                        Task(1, 70),
                        Task(9, 81)))
    testPath = 'test_fileOutput2Setups.txt'
    cleanFile(testPath)
    sof = DPOutputFile(testPath)
    sof.write(*rmlSetups(*tasksets))

    expectedFileContent = ('1 40 40 39 4 -4\n'
                           '11 46 46 34 3 -3\n'
                           '35 56 56 0 2 -2\n'
                           '10 99 99 99 1 1\n'
                           '\n'
                           '14 40 40 26 4 -4\n'
                           '36 69 69 5 3 -3\n'
                           '1 70 70 5 2 -2\n'
                           '9 81 81 81 1 1\n'
                           '\n')

    with open(testPath) as file:
        fileContent = file.read()
        assert fileContent == expectedFileContent
    cleanFile(testPath)

