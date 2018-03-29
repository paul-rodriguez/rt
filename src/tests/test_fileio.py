from crpd.fileio import SetupInputFile
from crpd.model import Taskset, Task
from crpd.sim import SimulationSetup
from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo


def test_fileInput():
    Task.resetIdCounter()
    sif = SetupInputFile('${HOME}/git/rt/tasksets/test.txt')
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
