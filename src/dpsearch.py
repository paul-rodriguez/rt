"""
Usage:
    dpsearch.py NBSYSTEMS [-s SEED] [-h] [-c CORES] [-P|-l]

Options:
    -P          Disable LPV preprocessing.
    -l          Only list LPV tasks, do not simulate.
    -s SEED     Seed of the random number generator used to create task sets.
                [default: 1337]
    -c CORES    Number of processes to spawn.
"""

from concurrent.futures import ProcessPoolExecutor
from docopt import docopt
import logging
import itertools

from crpd.gen import TasksetGenerator, RandomValue, PeriodGenerator
from crpd.sim import SimulationSetup, SimulationRun
from dualpriority.policies import (rmLaxityPromotions,
                                   fpRMResponseTimes,
                                   genLpViableTasks,
                                   dajamPromotions)
from dualpriority.utils import rmSortedTasks


def genTasksets(nbTasksets, seed, periodInterval, nbTasks):
    gen = TasksetGenerator(seed=seed,
                           scale=1,
                           nbTasks=RandomValue(value=nbTasks),
                           periodGenerator=PeriodGenerator(
                               interval=periodInterval),
                           utilization=RandomValue(floatrange=(0.9, 1.0)))

    def filterHyperperiod():
        validSystems = 0
        while validSystems < nbTasksets:
            taskset = gen()
            if taskset.hyperperiod < 10000000:
                validSystems += 1
                logging.info('Generated system hyperperiod: %s',
                             taskset.hyperperiod)
                yield taskset
            else:
                logging.info('Discarded hyperperiod: %s',
                             taskset.hyperperiod)

    return list(filterHyperperiod())


def equalPeriodTest(taskset, policy):
    rmTaskset = rmSortedTasks(taskset)
    leastPromotedTask = rmTaskset[-2]
    if policy.hasPromotion(leastPromotedTask):
        lastTask = rmTaskset[-1]
        lastTPeriod = lastTask.minimalInterArrivalTime
        lpPeriod = leastPromotedTask.minimalInterArrivalTime
        rmRT = fpRMResponseTimes(taskset)
        responseTime = rmRT[leastPromotedTask]
        if responseTime > lpPeriod:
            logging.warning('Task 2 misses deadlines in RM')
            if lastTPeriod != lpPeriod:
                logging.critical('Detected inconsistency')


def execFunction(taskset, lpvPrep):
    policy = rmLaxityPromotions(taskset, lpvPrep=lpvPrep)
    if len(policy.promotedTasks()) > 0:
        setup = SimulationSetup(taskset,
                                taskset.hyperperiod,
                                schedulingPolicy=policy,
                                trackHistory=False,
                                trackPreemptions=False)
        result = SimulationRun(setup).result()
        history = result.history
    else:
        history = True
    return history, policy, taskset


def multicoreLoop(tasksets, nbProcesses, disablePrep):
    failures = set()
    with ProcessPoolExecutor(max_workers=nbProcesses) as executor:
        for result in executor.map(execFunction,
                                   tasksets,
                                   itertools.repeat(not disablePrep)):
            history, policy, taskset = result
            logging.info(taskset)
            logging.info('Hyperperiod: {}'.format(taskset.hyperperiod))
            logging.info('Utilization: {}'.format(taskset.utilization))
            logging.info('Result policy: %s', policy)
            if history is True:
                logging.info('All LPV')
            elif history.hasDeadlineMiss():
                failures.add(taskset)
                logging.warning('Deadline miss %s',
                                history.firstDeadlineMiss())
                logging.warning('For system %s', taskset)
                logging.warning('With policy %s', policy)
            else:
                logging.info('OK')
            if len(failures) > 0:
                logging.info('Current number of failures: %d', len(failures))
            else:
                logging.info('No failures')
    return failures


def allTasksets(base, top, period1, tasksetSizes, nbSystems, seed):
    for periodHi in range(base, top):
        periodInterval = (period1, periodHi)
        for nbTasks in tasksetSizes:
            tasksets = genTasksets(nbSystems,
                                   seed + periodHi,
                                   periodInterval,
                                   nbTasks)
            yield from tasksets


def runMcSearch(tasksets,
                nbProcesses,
                disablePrep,
                base,
                top,
                tasksetSizes,
                nbSystems):
    tasksets = sorted(tasksets, key=lambda x: -x.hyperperiod)

    def failuresDict(nbProcesses, disablePrep):
        failures = multicoreLoop(tasksets, nbProcesses, disablePrep)
        allFailures = {}
        for failure in failures:
            key = len(failure), failure.maxPeriod
            if key in allFailures:
                allFailures[key].append(failure)
            else:
                allFailures[key] = [failure]
        return allFailures

    failures = failuresDict(nbProcesses, disablePrep)
    for nbTasks in tasksetSizes:
        for periodHi in range(base, top):
            try:
                nbf = len(failures[(nbTasks, periodHi)])
            except KeyError:
                nbf = 0
            print('Number of failures for {} tasks periodHi {}: '
                  '{}/{}'.format(nbTasks, periodHi, nbf, nbSystems))
    print('Failures: {}'.format(failures.values()))


def runLPVSearch(tasksets):
    nbFullLPV = 0
    nbNoLPV = 0
    total = 0
    nbLPVTasks = 0
    nbTasks = 0
    for taskset in tasksets:
        lpvTasks = list(genLpViableTasks(taskset))
        nbLpv = len(lpvTasks)
        nbLPVTasks += nbLpv
        nbTasks += len(taskset)
        total += 1
        if nbLpv > 0:
            if nbLpv == len(taskset):
                nbFullLPV += 1
            print('{}/{} LPV Tasks {} \n'
                  'for taskset {}'.format(len(lpvTasks), len(taskset),
                                          lpvTasks, taskset))
            policy = rmLaxityPromotions(taskset)
            print('Policy {}'.format(policy))
        else:
            nbNoLPV += 1
            print('No LPV')
    print('Nb full LPV: {}'.format(nbFullLPV))
    print('Nb no LPV: {}'.format(nbNoLPV))
    print('Total: {}'.format(total))

    print('Fraction of LPV tasks: {}'.format(nbLPVTasks / nbTasks))


def main(args):
    nbSystems = int(args['NBSYSTEMS'])
    seed = int(args['-s'])
    disablePrep = args['-P']
    if args['-c']:
        nbProcesses = int(args['-c'])
    else:
        nbProcesses = None

    logging.info(
        'Running dpsearch on {} systems with seed {}'.format(nbSystems,
                                                             seed))
    # period1 = 40
    # base = 50
    # top = 120
    # tasksetSizes = [3, 4, 5]

    period1 = 24
    base = 50
    top = 91
    tasksetSizes = [3]

    tasksets = list(allTasksets(base,
                                top,
                                period1,
                                tasksetSizes,
                                nbSystems,
                                seed))

    if not args['-l']:
        runMcSearch(tasksets,
                    nbProcesses,
                    disablePrep,
                    base,
                    top,
                    tasksetSizes,
                    nbSystems)
    else:
        runLPVSearch(tasksets)


if __name__ == '__main__':
    args = docopt(__doc__)

    logging.basicConfig(level=logging.INFO)
    main(args)
