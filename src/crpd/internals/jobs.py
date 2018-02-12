import logging

from ..hist import JobState, Preemption
from .events import Deadline, Arrival


logger = logging.getLogger(__name__)


class JobManager:

    def __init__(self, jobStates):
        self._jobs = {}
        for js in jobStates:
            job = Job(jobState=js)
            self._jobs[(job.task, job.releaseIndex)] = job

    def jobs(self):
        return self._jobs.values()

    def removeJob(self, job):
        entry = (job.task, job.releaseIndex)
        try:
            del self._jobs[entry]
        except KeyError as e:
            keys = set(self._jobs.keys())
            logger.exception('Job not found at deadline: %s\n'
                             'In set of jobs: %s', entry, keys)
            raise e

    def getJob(self, task, releaseIndex):
        entry = (task, releaseIndex)
        if entry in self._jobs:
            job = self._jobs[entry]
        else:
            job = Job(task, releaseIndex)
            self._jobs[entry] = job
        return job


class Job:

    def __init__(self, task=None, releaseIndex=0, jobState=None):
        if jobState is not None:
            self._task = jobState.task
            self._releaseIndex = jobState.releaseIndex
            self._progress = jobState.progress
            self._preemptionDebt = jobState.preemptionDebt
            self._lastStart = jobState.lastStart
        else:
            assert task is not None
            self._task = task
            self._releaseIndex = releaseIndex
            self._progress = 0
            self._preemptionDebt = 0
            self._lastStart = None

    def jobState(self):
        return JobState(self._task,
                        self._releaseIndex,
                        self._progress,
                        self._preemptionDebt,
                        self._lastStart)

    @property
    def task(self):
        return self._task

    @property
    def releaseTime(self):
        return self._task.arrivalTime(self._releaseIndex)

    @property
    def releaseIndex(self):
        return self._releaseIndex

    @property
    def deadline(self):
        return self._task.deadline + self.releaseTime

    @property
    def wcet(self):
        return self._task.wcet

    @property
    def taskId(self):
        return self._task.uniqueId

    def arrivalEvent(self):
        return Arrival(self.releaseTime, self)

    def deadlineEvent(self):
        return Deadline(self.deadline, self)

    def hasBeenStarted(self):
        return self._lastStart is not None

    def isCompleted(self):
        return self.remainingWcet() == 0 and self._preemptionDebt == 0

    def lastStart(self):
        return self._lastStart

    def progress(self):
        return self._progress

    def remainingExecWithDebt(self):
        return self.remainingWcet() + self._preemptionDebt

    def remainingWcet(self):
        return self.wcet - self._progress

    def preemptionDebt(self):
        return self._preemptionDebt

    def progressTo(self, time):
        increment = time - self._lastStart
        assert(increment >= 0)
        if increment >= self._preemptionDebt:
            remainingIncrement = increment - self._preemptionDebt
            self._preemptionDebt = 0
        else:
            self._preemptionDebt = self._preemptionDebt - increment
            remainingIncrement = 0
        self._lastStart = time
        self._progress += remainingIncrement

    def preemption(self, time, preemptingJob):
        preemptionCostModel = self._task.preemptionCost
        cost = preemptionCostModel.cost(self)
        previousDebt = self._preemptionDebt
        self._preemptionDebt = cost
        preemption = Preemption(time,
                                self.task,
                                self.releaseIndex,
                                preemptingJob.task,
                                preemptingJob.releaseIndex,
                                cost,
                                previousDebt)
        logger.debug('Preemption of %s, set debt to %s', self, cost)
        return preemption

    def stop(self):
        self._lastStart = None

    def start(self, time):
        self._lastStart = time

    def __repr__(self):
        return ('Job({}, I {}, R {}, P {}, D {}'
                ', L {})').format(self._task,
                                  self._releaseIndex,
                                  self.releaseTime,
                                  self._progress,
                                  self._preemptionDebt,
                                  self._lastStart)

    def __lt__(self, other):
        raise NotImplementedError

    def __le__(self, other):
        raise NotImplementedError

    def __gt__(self, other):
        raise NotImplementedError

    def __ge__(self, other):
        raise NotImplementedError
