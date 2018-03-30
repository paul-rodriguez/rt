import logging

from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationSetup, SimulationRun
from crpd.stats import AggregatorTag
from .internals import (
    rmSortedTasks,
    minusRmSortedTasks,
    baseRMPolicy,
    getHistory,
    baseRMRMPolicy,
    findFirstDeadlineMiss,
    fixRMRMPolicy,
)

logger = logging.getLogger(__name__)


class ValidPromotionNotFound(Exception):
    pass


def dajamPromotions(taskset):
    rmSortedTaskset = rmSortedTasks(taskset)

    maxPrio = len(taskset)

    lpViableTasks = list(genLpViableTasks(rmSortedTaskset))
    nbViableTasks = len(lpViableTasks)
    promotedTasks = rmSortedTaskset[:-(1 + nbViableTasks)]

    def genPromotions():
        antiWcets = [task.minimalInterArrivalTime - task.wcet
                     for task in rmSortedTaskset]
        return {task: min(antiWcets[:i + 1])
                for i, task in enumerate(rmSortedTaskset)}

    def genPrios():
        promoDict = dict(genPromotions())
        for i, task in enumerate(promotedTasks):
            promotion = promoDict[task]
            yield (task,
                   DualPriorityTaskInfo(maxPrio - i, promotion, i - maxPrio))
        if nbViableTasks < len(taskset):
            yield (rmSortedTaskset[-(1 + nbViableTasks)],
                   DualPriorityTaskInfo(1))
        for i, task in enumerate(reversed(lpViableTasks)):
            prio = maxPrio + nbViableTasks + i
            yield (task,
                   DualPriorityTaskInfo(prio))

    policy = DualPrioritySchedulingPolicy(*genPrios())
    return policy


def greedyDeadlineFixPolicy(taskset):
    """
    Returns a RM/RM DP policy with promotion times set according to a greedy
    process that gradually decrements promotions to fix deadline misses.
    """
    policy = baseRMRMPolicy(taskset)
    dm = findFirstDeadlineMiss(taskset, policy)
    while dm is not None:
        policy = fixRMRMPolicy(policy, dm)
        dm = findFirstDeadlineMiss(taskset, policy)
    return policy


def rmLaxityPromotions(taskset, lpvPrep=True):
    """
    Returns a DP policy with promotion times setup following the worst case RM
    laxity technique.

    That is, the promotions of all tasks except the longest one are set equal
    to their worst case (i.e. smallest) RM laxity.
    Tasks that are least priority viable in RM are left on the lowest priority
    band (but only if lpvPrep is True, otherwise they are treated the same).
    """
    rmSortedTaskset = rmSortedTasks(taskset)
    longestResponseTimes = fpRMResponseTimes(taskset)

    maxPrio = len(taskset)

    if lpvPrep:
        lpViableTasks = list(genLpViableTasks(rmSortedTaskset))
    else:
        lpViableTasks = []
    nbViableTasks = len(lpViableTasks)
    promotedTasks = rmSortedTaskset[:-(1 + nbViableTasks)]

    def genPrios():
        for i, task in enumerate(promotedTasks):
            taskResponseTime = longestResponseTimes[task]
            rmLaxity = task.minimalInterArrivalTime - taskResponseTime
            promotion = rmLaxity if rmLaxity > 0 else 0
            yield (task,
                   DualPriorityTaskInfo(maxPrio - i, promotion, i - maxPrio))
        if nbViableTasks < len(taskset):
            yield (rmSortedTaskset[-(1 + nbViableTasks)],
                   DualPriorityTaskInfo(1))
        for i, task in enumerate(reversed(lpViableTasks)):
            prio = maxPrio + nbViableTasks + i
            yield (task,
                   DualPriorityTaskInfo(prio))

    policy = DualPrioritySchedulingPolicy(*genPrios())
    return policy


def dichotomicPromotionSearch(taskset):
    """
    Returns a DP policy with appropriate promotion times for the taskset.

    The promotion times are found by dichotomic search.
    If some tasks don't require promotions or if some of the longer tasks are
    schedulable with RM, the search takes that into account.
    """

    lpViableTasks = list(genLpViableTasks(taskset))
    basePolicy = _baseLPVPolicy(taskset, lpViableTasks)
    dualInclude = set(taskset) - set(lpViableTasks)
    startMinusRMPolicy = _setupPolicyForDual(dualInclude, basePolicy)
    rmSortedIncluded = rmSortedTasks(dualInclude)
    builtPolicy = _loopTasksToPromote(rmSortedIncluded,
                                      set(lpViableTasks),
                                      taskset,
                                      startMinusRMPolicy)
    cleanPolicy = _cleanRMm1RMpolicy(builtPolicy)
    return cleanPolicy


def _cleanRMm1RMpolicy(policy):
    def genInfo():
        sortedInfo = sorted(policy.items(), key=lambda x: x[1].lowPriority)
        firstTask, _ = sortedInfo[0]
        yield firstTask, DualPriorityTaskInfo(1)
        spuriousPromo = True
        for task, info in sortedInfo[1:]:
            spuriousPromo = (spuriousPromo and
                             info.hasPromotion and
                             task.minimalInterArrivalTime == info.promotion)
            if spuriousPromo:
                newInfo = DualPriorityTaskInfo(info.lowPriority)
                yield task, newInfo
            else:
                yield task, info

    return DualPrioritySchedulingPolicy(*genInfo())


def _baseLPVPolicy(taskset, lpViableTasks):
    maxPrio = len(taskset)

    def genPrios():
        for i, task in enumerate(reversed(lpViableTasks)):
            prio = maxPrio + len(lpViableTasks) + i
            yield (task, DualPriorityTaskInfo(prio))

    policy = DualPrioritySchedulingPolicy(*genPrios())
    return policy


def genLpViableTasks(taskset):
    """
    Generate LPV tasks of the taskset, in order.

    The first generated task is viable at the smallest priority level.
    The second task is viable at the level just above that, and so on.
    """

    remainingTasks = set(taskset)

    def findLpv(remainingTasks):
        for task in remainingTasks:
            interferingTasks = [t for t in remainingTasks if t is not task]
            taskResponseTime = responseTime(task, interferingTasks)
            laxity = task.minimalInterArrivalTime - taskResponseTime
            if laxity >= 0:
                return task
        return None

    while remainingTasks:
        lpvTask = findLpv(remainingTasks)
        if lpvTask is not None:
            yield lpvTask
            remainingTasks.remove(lpvTask)
        else:
            break


def _dajamPromo(taskset, task):
    hyperperiod = taskset.hyperperiod

    def deadlines():
        time = task.minimalInterArrivalTime
        while time <= hyperperiod:
            yield time
            time += task.minimalInterArrivalTime

    def worklist(time):
        for task in taskset:
            period = task.minimalInterArrivalTime
            work = (time // period) * task.wcet
            yield work

    def laxities():
        for deadline in deadlines():
            work = sum(worklist(deadline))
            yield deadline - work

    promo = min(laxities())
    return promo


def _simuRMResponseTimes(taskset):
    rmPolicy = baseRMPolicy(taskset)
    hyperperiod = taskset.hyperperiod
    aggregators = (AggregatorTag.LongestResponseTime,)
    setup = SimulationSetup(taskset,
                            time=hyperperiod,
                            schedulingPolicy=rmPolicy,
                            aggregatorTags=aggregators,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    longestResponseTimes = result.aggregateStat(
          AggregatorTag.LongestResponseTime)
    return longestResponseTimes


def responseTime(task, interferingTasks):
    def interferences(time):
        for t in interferingTasks:
            w = t.wcet
            period = t.minimalInterArrivalTime
            result = w * (1 + ((time - 1) // period))
            yield result

    rt = 0
    nextRt = task.wcet
    limit = task.deadline * 2
    while rt < nextRt < limit:
        rt = nextRt
        intf = interferences(rt)
        interferenceTotal = sum(intf)
        nextRt = task.wcet + interferenceTotal
    if nextRt > limit:
        nextRt = limit
    return nextRt


def fpRMResponseTimes(taskset):
    rmSorted = rmSortedTasks(taskset)

    def shorterTasks(task):
        for t in rmSorted:
            if t is task:
                break
            yield t

    def interferences(task, time):
        for t in shorterTasks(task):
            w = t.wcet
            period = t.minimalInterArrivalTime
            result = w * (1 + ((time - 1) // period))
            yield result

    def genDict():
        for task in taskset:
            rt = 0
            nextRt = task.wcet
            limit = task.deadline * 2
            while rt < nextRt < limit:
                rt = nextRt
                intf = interferences(task, rt)
                interferenceTotal = sum(intf)
                nextRt = task.wcet + interferenceTotal
            if nextRt > limit:
                nextRt = limit
            yield task, nextRt

    return dict(genDict())


def _setupPolicyForDual(includeSet, basePolicy):
    rmSorted = rmSortedTasks(includeSet)
    maxPrio = len(includeSet)

    def genPrios():
        for index, task in enumerate(rmSorted):
            deadline = task.deadline
            minusRmPriority = maxPrio - index
            highPrio = -minusRmPriority
            schedInfo = DualPriorityTaskInfo(minusRmPriority,
                                             deadline,
                                             highPrio)
            yield task, schedInfo

    return basePolicy.withUpdate(*genPrios())


def _loopTasksToPromote(tasksToPromote,
                        tasksToTest,
                        taskset,
                        policy):
    if not tasksToPromote:
        return policy
    taskToPromote = tasksToPromote[0]
    newTasksToPromote = tasksToPromote[1:]
    newTasksToTest = tasksToTest.union({taskToPromote})
    maxPromo = policy.promotion(taskToPromote)
    updatedPolicy = _loopTaskPromotion(taskToPromote,
                                       newTasksToPromote,
                                       newTasksToTest,
                                       taskset,
                                       policy,
                                       0,
                                       maxPromo)
    return updatedPolicy


def _successForTasks(tasksToTest, taskset, policy):
    history = getHistory(taskset, policy, *tasksToTest)
    hasDeadlineMiss = any(len(history.deadlineMisses(taskset.hyperperiod,
                                                     task=t)) > 0
                          for t in tasksToTest)
    return not hasDeadlineMiss


def _removedPromotions(tasks, policy):
    def genPrios():
        for task in tasks:
            lowPrio = policy.lowPriority(task)
            newInfo = DualPriorityTaskInfo(lowPrio)
            yield task, newInfo

    return policy.withUpdate(*genPrios())


def _copyWithPromotion(task, policy, promotion):
    lowPrio = policy.lowPriority(task)
    highPrio = policy.highPriority(task)
    newInfo = DualPriorityTaskInfo(lowPrio, promotion, highPrio)
    updatedPolicy = policy.withUpdate((task, newInfo))
    return updatedPolicy


def _loopTaskPromotion(taskToPromote,
                       tasksToPromote,
                       tasksToTest,
                       taskset,
                       policy,
                       minPromo,
                       maxPromo):
    promotion = (minPromo + maxPromo) // 2
    updatedPolicy = _copyWithPromotion(taskToPromote, policy, promotion)
    hasDeadlineMiss = not _successForTasks(tasksToTest,
                                           taskset,
                                           updatedPolicy)
    failed = hasDeadlineMiss
    if not hasDeadlineMiss:
        try:
            endPolicy = _loopTasksToPromote(tasksToPromote,
                                            tasksToTest,
                                            taskset,
                                            updatedPolicy)
        except ValidPromotionNotFound:
            failed = True

    if failed:
        if promotion == 0:
            raise ValidPromotionNotFound
        endPolicy = _loopTaskPromotion(taskToPromote,
                                       tasksToPromote,
                                       tasksToTest,
                                       taskset,
                                       updatedPolicy,
                                       minPromo,
                                       promotion)
    return endPolicy


def _rmExcludedTasks(taskset, history):
    def gen():
        for task in minusRmSortedTasks(taskset):
            failures = history.deadlineMisses(taskset.hyperperiod,
                                              task=task)
            if not failures:
                yield task
            else:
                break

    return set(gen())
