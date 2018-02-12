import logging
from heapq import heapify, heappop, heappush

from .events import Completion, ScheduleTick, convertStateEvent
from .jobs import JobManager
from .sched import SchedulerFactory
from ..hist import SimulatorState, DeadlineMiss


logger = logging.getLogger(__name__)


class Simulator:

    def __init__(self,
                 taskset,
                 history,
                 state,
                 trackHistory=True,
                 trackPreemptions=True,
                 statAggregators=None):
        self._taskset = taskset
        self._time = state.time
        self._historyManager = _HistoryManager(history,
                                               state,
                                               trackHistory,
                                               trackPreemptions,
                                               statAggregators)
        self._eventQueue = None
        self._scheduler = None
        self._jobManager = None
        self._stopOnMiss = False

    def simulateTo(self, timeLimit, stopOnMiss=False):
        logger.debug('Simulating to %s', timeLimit)
        self._stopOnMiss = stopOnMiss
        if stopOnMiss:
            logger.debug('Stopping on deadline miss')
        continueSimu = False
        if self._time < timeLimit:
            self._initFromState()
            continueSimu = self._executeEvents(timeLimit)
        while continueSimu:
            self._doSchedule()
            self._nextState(force=False)
            continueSimu = self._executeEvents(timeLimit)
        self._simulationEpilogue(timeLimit)

    def arrival(self, job):
        self._scheduler.addReadyJob(job)
        self._eventQueue.addDeadline(job)
        nextRelease = self._jobManager.getJob(job.task, job.releaseIndex + 1)
        self._eventQueue.addArrival(nextRelease)

    def deadline(self, job):
        if not job.isCompleted():
            logger.debug('Deadline miss at time %s for job %s',
                         job.deadline, job)
            self._historyManager.addDeadlineMiss(job)
        else:
            self._jobManager.removeJob(job)

    def completion(self, job):
        job.progressTo(self._time)
        logger.debug('Job complete: %s', job)
        try:
            assert(job == self._scheduler.runningJob())
        except AssertionError as e:
            logger.exception('Running job %s is not the same as %s',
                             self._scheduler.runningJob(), job)
            raise e
        self._scheduler.executionCompleted()
        if job.deadline < self._time:
            self._jobManager.removeJob(job)

    def _preempt(self, preemptedJob, preemptingJob):
        preemptedJob.progressTo(self._time)
        preemptedJob.stop()
        preemption = preemptedJob.preemption(self._time, preemptingJob)
        self._execute(preemptingJob)
        self._historyManager.addPreemption(preemption)

    def _execute(self, job):
        job.start(self._time)
        self._addCompletionEvent(job)

    def _addCompletionEvent(self, job):
        completionTime = self._time + job.remainingExecWithDebt()
        completion = Completion(completionTime, job)
        self._eventQueue.addEvent(completion)

    def _initFromState(self):
        jobStates = self._historyManager.currentJobStates()
        self._jobManager = JobManager(jobStates)
        eventStates = self._historyManager.currentEventStates()
        events = [convertStateEvent(self._jobManager, e) for e in eventStates]
        self._eventQueue = _EventQueue(events)
        schedulerState = self._historyManager.currentSchedulerState()
        self._scheduler = SchedulerFactory.fromState(schedulerState,
                                                     self._jobManager)
        self._scheduler.initializeSchedulerData(self._taskset)
        self.addNextScheduleTicks()

    def _simulationEpilogue(self, timeLimit):
        if not self._deadlineMissCheck():
            logger.debug('Stopping due to deadline miss(es) %s',
                         self._historyManager.currentDeadlineMisses())
            self._nextState(force=True)
        elif self._time < timeLimit:
            self._refreshSimu(timeLimit)
        else:
            self._nextState(force=True)

    def _refreshSimu(self, time):
        logger.debug('Refreshing state from %s to %s', self._time, time)
        runningJob = self._scheduler.runningJob()
        if runningJob is not None:
            runningJob.progressTo(time)
        self._time = time
        self._nextState(force=True)

    def _nextState(self, force=False):
        jobs = self._jobManager.jobs()
        events = self._eventQueue.events()
        self._historyManager.nextState(self._time,
                                       jobs,
                                       events,
                                       self._scheduler,
                                       forceAdd=force)

    def _deadlineMissCheck(self):
        if self._stopOnMiss:
            return not self._historyManager.deadlineMissOccured()
        else:
            return True

    def _executeEvents(self, timeLimit):
        top = self._eventQueue.top()
        try:
            assert(top.time >= self._time)
        except AssertionError:
            logger.exception('Reversing time, top: %s', top)
            raise
        if top.time < timeLimit:
            self._time = top.time
            logger.debug("Changed time to %d", top.time)
            timeChanged = False
            while not timeChanged:
                top = self._eventQueue.effectiveTop()
                assert top.time >= self._time
                if top.time == self._time:
                    logger.debug("Executing event: %s", top)
                    self._eventQueue.pop()
                    top.execute(self)
                else:
                    timeChanged = True
            return self._deadlineMissCheck()
        else:
            return False

    def _doSchedule(self):
        oldJob, newJob = self._scheduler.schedule(self._time)
        if newJob is not None:
            if oldJob is not None:
                if oldJob is not newJob:
                    self._preempt(oldJob, newJob)
                else:
                    newJob.progressTo(self._time)
            else:
                self._execute(newJob)

    def addNextScheduleTicks(self):
        scheduleTicks = self._scheduler.nextScheduleTicks(self._time)
        for scheduleTick in scheduleTicks:
            self._eventQueue.addScheduleTick(scheduleTick)


class _EventQueue:

    def __init__(self, events=None):
        if events is None:
            events = []
        self._queue = [(e.time, e.priority, e) for e in events]
        heapify(self._queue)

    def effectiveTop(self):
        top = self.top()
        while top.ignore():
            logger.debug("Event ignored: %s", top)
            self.pop()
            top = self.top()
        return top

    def top(self):
        _, _, event = self._queue[0]
        return event

    def pop(self):
        try:
            heappop(self._queue)
        except TypeError:
            logger.exception('Queue content {}'.format(self._queue))
            raise

    def events(self):
        for _, _, e in self._queue:
            yield e

    def addDeadline(self, job):
        self.addEvent(job.deadlineEvent())

    def addArrival(self, job):
        self.addEvent(job.arrivalEvent())

    def addScheduleTick(self, time):
        self.addEvent(ScheduleTick(time))

    def addEvent(self, event):
        logger.debug('Adding event %s', event)
        entry = (event.time, event.priority, event)
        heappush(self._queue, entry)


class _HistoryManager:

    def __init__(self,
                 history,
                 initialState,
                 trackHistory,
                 trackPreemptions,
                 aggregators):
        self._history = history
        self._currentState = initialState
        self._trackHistory = trackHistory
        self._trackPreemptions = trackPreemptions
        self._currentDeadlineMisses = []
        self._currentPreemptions = []
        self._aggregators = aggregators

    def currentDeadlineMisses(self):
        return self._currentDeadlineMisses

    def deadlineMissOccured(self):
        return len(self._currentDeadlineMisses) > 0

    def preemptionOccured(self):
        return len(self._currentPreemptions) > 0

    def addDeadlineMiss(self, job):
        deadlineMiss = DeadlineMiss(job.task, job.releaseIndex)
        self._currentDeadlineMisses.append(deadlineMiss)

    def addPreemption(self, preemption):
        self._currentPreemptions.append(preemption)

    def currentJobStates(self):
        return self._currentState.jobs

    def currentEventStates(self):
        return self._currentState.events

    def currentSchedulerState(self):
        return self._currentState.scheduler

    def nextState(self, time, jobs, events, scheduler, forceAdd=False):
        trackCond = self._trackingCondition()
        if self._aggregators or forceAdd or trackCond:
            eventList = list(events)
        if forceAdd or trackCond:
            nextState = self._createState(time, jobs, eventList, scheduler)
            self._history.addState(nextState)
            self._currentState = nextState
        if self._aggregators:
            self._updateAggregators(time,
                                    jobs,
                                    eventList,
                                    scheduler)
        self._currentDeadlineMisses.clear()
        self._currentPreemptions.clear()

    def _updateAggregators(self, time, jobs, events, scheduler):
        for aggregator in self._aggregators:
            aggregator.aggregate(time,
                                 jobs,
                                 events,
                                 scheduler,
                                 self._currentDeadlineMisses,
                                 self._currentPreemptions)

    def _createState(self, time, jobs, events, scheduler):
        jobStates = [j.jobState() for j in jobs]
        events = [e.stateConverted() for e in events]
        schedulerState = scheduler.schedulerState()
        state = SimulatorState(time,
                               jobStates,
                               events,
                               self._currentDeadlineMisses,
                               preemptions=self._currentPreemptions,
                               scheduler=schedulerState)
        return state

    def _trackingCondition(self):
        return (self._trackHistory or
                self.deadlineMissOccured() or
                (self._trackPreemptions and self.preemptionOccured()))
