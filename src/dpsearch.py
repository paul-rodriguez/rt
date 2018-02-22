"""
Usage:
    dpsearch.py NBSYSTEMS [-s SEED] [-h] [-c CORES] [-P|-l] \
[--period1 PERIOD1] [--pBase PBASE] [--pTop PTOP] [--tSizes TSIZES] \
[--uRange URANGE]

Options:
    -P          Disable LPV preprocessing.
    -l          Only list LPV tasks, do not simulate.
    -s SEED     Seed of the random number generator used to create task sets.
                [default: 1337]
    -c CORES    Number of processes to spawn.

Taskset generation options:
    --period1 PERIOD1    Smallest period in the taskset. [default: 24]
    --pBase PBASE        Base of the interval of greater periods. [default: 50]
    --pTop PTOP          Top of the interval of greater periods. [default: 90]
    --tSizes TSIZES      Comma-separated list of taskset sizes. [default: 3]
    --uRange URANGE      Interval of taskset utilisations [default: 0.9,1.0]
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


def genTasksets(nbTasksets, seed, periodInterval, nbTasks, uRange):
    gen = TasksetGenerator(seed=seed,
                           scale=1,
                           nbTasks=RandomValue(value=nbTasks),
                           periodGenerator=PeriodGenerator(
                               interval=periodInterval),
                           utilization=RandomValue(floatrange=uRange))

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


def allTasksets(base, top, period1, tasksetSizes, nbSystems, seed, uRange):
    for periodHi in range(base, top):
        periodInterval = (period1, periodHi)
        for nbTasks in tasksetSizes:
            tasksets = genTasksets(nbSystems,
                                   seed + periodHi,
                                   periodInterval,
                                   nbTasks, uRange)
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

    period1 = int(args['--period1'])
    base = int(args['--pBase'])
    top = int(args['--pTop']) + 1
    tSizeStr = args['--tSizes']
    uRange = [float(s) for s in args['--uRange'].split(',')]
    tasksetSizes = [int(s) for s in tSizeStr.split(',')]

    tasksets = list(allTasksets(base,
                                top,
                                period1,
                                tasksetSizes,
                                nbSystems,
                                seed,
                                uRange))

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
