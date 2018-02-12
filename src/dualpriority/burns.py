
import logging

from .utils import rmSortedTasks, baseRMPolicy, getHistory
from crpd.hist import DeadlineMissFilter
from crpd.sim import Simulation


def burnsWellingsPolicy(taskset):
    rmSorted = rmSortedTasks(taskset)
    lastTask = rmSorted[-1]
    policy = baseRMPolicy(taskset)
    simu = Simulation(taskset, policy)
    dmFilter = DeadlineMissFilter(False, lastTask)
    state = simu.firstDeadlineMiss(dmFilter)
    deadlineMiss = relevantDeadlineMiss(state, lastTask)
    missingExecution(deadlineMiss, state)

    logging.warning('%s', state)
    return policy


def missingExecution(deadlineMiss, state):

    def findJobState(task, releaseIndex, jobStates):
        for js in jobStates:
            if js.task is task and js.releaseIndex == releaseIndex:
                return js
        raise AssertionError

    task = deadlineMiss.task
    jobState = findJobState(task, deadlineMiss.releaseIndex, state.jobs)
    logging.warning('%s', jobState)


def relevantDeadlineMiss(state, task):
    dmSet = state.deadlineMisses
    for dm in dmSet:
        if dm.task is task:
            return dm
    raise AssertionError


def countExecution(history, priority, interval):
    """
    Count the amount of execution that can be stolen in a time interval at
    higher than the given priority level.

    :param history:
    :param priority:
    :param interval:
    :return:
    """
    pass

