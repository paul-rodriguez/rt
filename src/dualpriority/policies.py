
import logging

from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationSetup, SimulationRun
from crpd.stats import AggregatorTag
from .utils import (rmSortedTasks,
                    minusRmSortedTasks,
                    baseRMPolicy,
                    getHistory)

logger = logging.getLogger(__name__)


def dajamPromotions(taskset):
    rmSortedTaskset = rmSortedTasks(taskset)

    maxPrio = len(taskset)

    lpViableTasks = list(genLpViableTasks(rmSortedTaskset))
    nbViableTasks = len(lpViableTasks)
    promotedTasks = rmSortedTaskset[:-(1 + nbViableTasks)]

    def genPromotions():
        antiWcets = [task.minimalInterArrivalTime - task.wcet
                     for task in rmSortedTaskset]
        return {task: min(antiWcets[:i+1])
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
    promotedTasks = rmSortedTaskset[:-(1+nbViableTasks)]

    def genPrios():
        for i, task in enumerate(promotedTasks):
            taskResponseTime = longestResponseTimes[task]
            rmLaxity = task.minimalInterArrivalTime - taskResponseTime
            promotion = rmLaxity if rmLaxity > 0 else 0
            yield (task,
                   DualPriorityTaskInfo(maxPrio - i, promotion, i - maxPrio))
        if nbViableTasks < len(taskset):
            yield (rmSortedTaskset[-(1+nbViableTasks)],
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

    rmPolicy = baseRMPolicy(taskset)
    history = getHistory(taskset, rmPolicy)
    dualExclude = _rmExcludedTasks(taskset, history)
    logger.info('Least priority viable: {}'.format(dualExclude))
    dualInclude = set(taskset) - dualExclude
    startMinusRMPolicy = _setupPolicyForDual(dualInclude, rmPolicy)
    rmSortedIncluded = rmSortedTasks(dualInclude)
    builtPolicy = _loopTasksToPromote(rmSortedIncluded,
                                      taskset,
                                      startMinusRMPolicy)
    return builtPolicy


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


def _setupPolicyForDual(includeSet, baseRMPolicy):
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

    return baseRMPolicy.withUpdate(*genPrios())


def _loopTasksToPromote(tasksToPromote,
                        taskset,
                        policy):
    if not tasksToPromote:
        return policy
    taskToPromote = tasksToPromote[0]
    newTasksToPromote = tasksToPromote[1:]
    passWithoutPromotion = _successForTask(taskToPromote, taskset, policy)
    if passWithoutPromotion:
        cleanedPolicy = _removedPromotions(tasksToPromote, policy)
        return cleanedPolicy
    else:
        maxPromo = policy.promotion(taskToPromote)
        promotion = _loopTaskPromotion(taskToPromote,
                                       taskset,
                                       policy,
                                       0,
                                       maxPromo)
        updatedPolicy = _copyWithPromotion(taskToPromote, policy, promotion)
        return _loopTasksToPromote(newTasksToPromote,
                                   taskset,
                                   updatedPolicy)


def _successForTask(promotedTask, taskset, policy):
    history = getHistory(taskset, policy, promotedTask)
    hasDeadlineMiss = len(history.deadlineMisses(taskset.hyperperiod,
                                                 task=promotedTask)) > 0
    return not hasDeadlineMiss


class _ValidPromotionNotFound(Exception):
    pass


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


def _loopTaskPromotion(taskToPromote, taskset, policy, minPromo, maxPromo):
    promotion = (minPromo + maxPromo) // 2
    updatedPolicy = _copyWithPromotion(taskToPromote, policy, promotion)
    hasDeadlineMiss = not _successForTask(taskToPromote,
                                          taskset,
                                          updatedPolicy)
    if hasDeadlineMiss:
        if promotion == 0:
            raise _ValidPromotionNotFound
        return _loopTaskPromotion(taskToPromote,
                                  taskset,
                                  updatedPolicy,
                                  minPromo,
                                  promotion)
    else:
        if maxPromo == minPromo + 1:
            logger.info('Assigning promotion %s for %s',
                        promotion,
                        taskToPromote)
            return promotion
        else:
            return _loopTaskPromotion(taskToPromote,
                                      taskset,
                                      updatedPolicy,
                                      promotion,
                                      maxPromo)


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

