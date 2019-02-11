'''
Usage:
    checkEkberg.py FILE
'''

from concurrent.futures import ProcessPoolExecutor
from datetime import timedelta
import docopt
from functools import reduce
import itertools
import operator
import math
import time

from crpd.model import Task, Taskset
from crpd.policy import DualPrioritySchedulingPolicy, DualPriorityTaskInfo
from crpd.sim import SimulationSetup, SimulationRun


def rmOrder(taskset):
    return sorted(taskset, key=lambda x: (x.arrivalDistribution.minimal,
                                          x.uniqueId))


def basePolicy(taskset):
    prioOffset = len(taskset)
    def genInfos():
        for i, task in enumerate(rmOrder(taskset)):
            yield (task,
                   DualPriorityTaskInfo(i,
                                        task.arrivalDistribution.minimal,
                                        i + prioOffset))

    return DualPrioritySchedulingPolicy(*genInfos())


def enumeratePriorities(taskset):
    nbPriorities = 2 * len(taskset)
    def recur(accPrio):
        if len(accPrio) == nbPriorities:
            yield accPrio
        else:
            prioRange = set(range(nbPriorities)).difference(accPrio)
            for prio in prioRange:
                yield from recur(accPrio + [prio])

    return recur([])


def enumeratePromotions(tasks):
    def recur(accPromo, remTasks):
        if not remTasks:
            yield accPromo
        else:
            task = remTasks[0]
            for promo in range(task.arrivalDistribution.minimal + 1):
                yield from recur(accPromo + [promo], remTasks[1:])

    return recur([], tasks)


def buildPolicy(tasks, priorities, promos):
    def generate():
        for index, task in enumerate(tasks):
            info = DualPriorityTaskInfo(priorities[(index * 2)],
                                        promos[index],
                                        priorities[(index * 2) + 1])
            yield task, info

    return DualPrioritySchedulingPolicy(*generate())


def enumeratePolicies(taskset):
    tasks = rmOrder(taskset)
    for priorities in enumeratePriorities(taskset):
        for promos in enumeratePromotions(tasks):
            yield buildPolicy(tasks, priorities, promos)


def execFunction(setup):
    taskset, policy = setup
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    return history.hasDeadlineMiss(), policy
    # resultStr = '/n'
    # resultStr += 'Simulation done: {}\n'.format(taskset)
    # if history.hasDeadlineMiss():
    #     resultStr += 'Deadline miss: {}\n'.format(history.firstDeadlineMiss())
    #     resultStr += 'With policy: {}\n'.format(policy)
    # else:
    #     resultStr += 'OK\n'
    # return resultStr


def runSimulations(setups, nbProcesses, output):
    setups = sorted(setups, key=lambda x: -x[0].hyperperiod)
    with ProcessPoolExecutor(max_workers=nbProcesses) as executor:
        for result in executor.map(execFunction,
                                      setups):
            hasDm, policy = result
            if not hasDm:
                output.write('{}\n'.format(policy))


def totalPolicies(taskset):
    nbPrioPermut = math.factorial(len(taskset) * 2)
    nbPromoSets = reduce(operator.mul,
                         (t.minimalInterArrivalTime + 1 for t in taskset),
                         1)
    return nbPrioPermut * nbPromoSets


def humanTime(seconds):
    return timedelta(seconds=int(seconds))


def main(args):
    print(args)


    nbProcesses = 12

    taskset = Taskset(Task(8, 19),
                      Task(13, 29),
                      Task(9, 151),
                      Task(14, 197))
    print(taskset)

    policyGen = enumeratePolicies(taskset)
    setups = ((taskset, policy) for policy in policyGen)

    chunkSize = 50000
    totalChunks = ((totalPolicies(taskset) - 1) // chunkSize) + 1
    setupSlice = list(itertools.islice(setups, chunkSize))
    chunkCnt = 0
    totalTime = 0
    while setupSlice:
        start = time.perf_counter()
        with open(args['FILE'], 'a', buffering=10000) as output:
            runSimulations(setupSlice, nbProcesses, output)
        end = time.perf_counter()
        chunkTime = end - start
        totalTime += chunkTime
        chunkCnt += 1
        averageChunkTime = totalTime / chunkCnt
        if chunkCnt > 0:
            expectedRemChunkTime = averageChunkTime * (totalChunks - chunkCnt)
        else:
            expectedRemChunkTime = 0
        print('Chunk {} / {} done. Time elapsed: {}. '
              'Chunk time: {:.4}s. '
              'Average chunk time: {:.4}s. '
              'Expected remaining time: {}.'.format(chunkCnt,
                                                     totalChunks,
                                                     humanTime(totalTime),
                                                     chunkTime,
                                                     averageChunkTime,
                                                     humanTime(expectedRemChunkTime)))
        setupSlice = list(itertools.islice(setups, chunkSize))


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)
