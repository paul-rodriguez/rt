from crpd.hist import DeadlineMissFilter
from crpd.policy import DualPriorityTaskInfo, DualPrioritySchedulingPolicy
from crpd.sim import SimulationSetup, SimulationRun


def rmSortedTasks(taskset):
    sortedTasks = sorted(taskset,
                         key=lambda x: (x.arrivalDistribution.minimal,
                                        x.uniqueId))
    return sortedTasks


def minusRmSortedTasks(tasks):
    sortedTasks = sorted(tasks,
                         key=lambda x: (-x.arrivalDistribution.minimal,
                                        -x.uniqueId))
    return sortedTasks


def baseRMPolicy(taskset):
    sortedTasks = rmSortedTasks(taskset)

    def taskPrios():
        for index, task in enumerate(sortedTasks):
            priority = index + 1
            yield task, DualPriorityTaskInfo(priority)

    policy = DualPrioritySchedulingPolicy(*taskPrios())
    return policy


def getHistory(taskset, policy, *stopTask):
    dmFilter = DeadlineMissFilter(False, *stopTask)

    setup = SimulationSetup(taskset,
                            time=taskset.hyperperiod,
                            deadlineMissFilter=dmFilter,
                            trackHistory=False,
                            trackPreemptions=False,
                            schedulingPolicy=policy)
    result = SimulationRun(setup).result()
    return result.history
