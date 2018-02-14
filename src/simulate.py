"""
Usage:
    simulate.py FILE [-c CORES]
    simulate.py -h|--help

Options:
    -h --help   Display this help text.
    -c CORES    Set the number of processes to spawn to execute the simulations
                in parallel.

Arguments:
    FILE        File containing task system descriptions with dual-priority
                priorities and promotion times.

Taskset description format:
    Each line of the file is either empty or describes a task with the following
    format:

    C T D S P1 P2

    Any sequence of whitespace characters is a valid delimiter.
    Empty lines delimit task sets, which means that:

    C T D S P1 P2

    C T D S P1 P2
    C T D S P1 P2

    C T D S P1 P2
    C T D S P1 P2
    C T D S P1 P2

    Is a file that contains three task sets.

    The file must always end with an empty line.
    None of the fields are allowed to contain negative values except P1 and P2.
    If a task is not promoted, its promotion must be equal to its deadline and
    its two priority values must be equal.
    Deadline and period must always be equal.
"""

from concurrent.futures import ProcessPoolExecutor
import docopt
import re

from crpd.model import Task, Taskset
from crpd.policy import DualPriorityTaskInfo, DualPrioritySchedulingPolicy
from crpd.sim import SimulationRun, SimulationSetup

REGEX = (r'([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+'
         '([-]?[0-9]+)\s+([0-9]+)\s+([-]?[0-9]+)')


def buildTask(c, t, d, s, p1, p2):
    assert t == d
    task = Task(int(c), int(d))
    if p1 < p2:
        raise AssertionError
    elif p1 == p2:
        dualPriorityInfo = DualPriorityTaskInfo(int(p1))
    else:
        dualPriorityInfo = DualPriorityTaskInfo(int(p1), int(s), int(p2))
    return task, dualPriorityInfo


def genTasks(file):
    line = file.readline()
    while line:
        m = re.match(REGEX, line)
        if not m:
            break
        else:
            yield buildTask(*m.groups())
            line = file.readline()


def genSetups(file):
    while file:
        pairs = list(genTasks(file))
        if not pairs:
            break
        tasks, dInfos = zip(*pairs)
        taskset = Taskset(*tasks)
        policy = DualPrioritySchedulingPolicy(*pairs)
        yield taskset, policy


def execFunction(setup):
    taskset, policy = setup
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            trackHistory=False,
                            trackPreemptions=False)
    result = SimulationRun(setup).result()
    history = result.history
    return history, policy, taskset


def runSimulations(setups, nbProcesses):
    setups = sorted(setups, key=lambda x: -x[0].hyperperiod)
    with ProcessPoolExecutor(max_workers=nbProcesses) as executor:
        for result in executor.map(execFunction,
                                   setups):
            history, policy, taskset = result
            print()
            print('Simulation done: {}'.format(taskset))
            if history.hasDeadlineMiss():
                print('Deadline miss: {}'.format(history.firstDeadlineMiss()))
                print('With policy: {}'.format(policy))
            else:
                print('OK')


def main(args):
    fileName = args['FILE']
    if args['-c']:
        nbProcesses = int(args['-c'])
    else:
        nbProcesses = None

    with open(fileName) as file:
        setups = list(genSetups(file))

    runSimulations(setups, nbProcesses)


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)
