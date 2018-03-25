
from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationRun, SimulationSetup, DeadlineMissFilter


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


def fixRMRMPolicy(brokenPolicy, deadlineMiss):
    task = deadlineMiss.task
    lowPrio = brokenPolicy.lowPriority(task)
    highPrio = brokenPolicy.highPriority(task)
    promotion = brokenPolicy.promotion(task)
    if promotion == 0:
        raise ValidPromotionNotFound
    newInfo = DualPriorityTaskInfo(lowPrio, promotion - 1, highPrio)
    updatedPolicy = brokenPolicy.withUpdate((task, newInfo))
    return updatedPolicy


def baseRMRMPolicy(taskset):
    def genPolicy():
        shift = len(taskset)
        rmSortedTaskset = rmSortedTasks(taskset)
        for priority, task in enumerate(rmSortedTaskset):
            tInfo = DualPriorityTaskInfo(priority,
                                         task.minimalInterArrivalTime,
                                         priority - shift)
            yield task, tInfo

    policy = DualPrioritySchedulingPolicy(*genPolicy())
    return policy


def findFirstDeadlineMiss(taskset, policy):
    setup = SimulationSetup(taskset,
                            time=taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    return history.firstDeadlineMiss()
