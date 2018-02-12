
import math
import logging
import random
from enum import Enum

from .model import Taskset, Task, FixedPreemptionCost, FixedArrivalDistribution

logger = logging.getLogger(__name__)

DEFAULT_SCALE = 1000


class RandomValue:

    def __init__(self,
                 value=None,
                 intrange=None,
                 floatrange=None,
                 logRange=None,
                 generator=None):
        """
        Use exactly one named argument.

        * `value` accepts a fixed value.
        * `intrange` accepts an interval that will be passed to random.randint
        * `floatrange` accepts an interval that will be passed to random.uniform
        * `generator` accepts a function with a return value
          You can use the random module in the generator function, it will be
          appropriately seeded.
        """
        if generator is not None:
            def gen():
                while True:
                    yield generator()
        elif intrange is not None:
            def gen():
                while True:
                    yield random.randint(*intrange)
        elif floatrange is not None:
            def gen():
                while True:
                    yield random.uniform(*floatrange)
        elif logRange is not None:
            a = math.log(logRange[0])
            b = math.log(logRange[1])

            def gen():
                while True:
                    yield math.exp(random.uniform(a, b))
        elif value is not None:
            def gen():
                while True:
                    yield value
        else:
            raise AssertionError
        self._values = gen()

    def __call__(self):
        return next(self._values)


class Periodicity(Enum):
    PERIODIC = 0
    SPORADIC = 1


class DeadlineCategory(Enum):
    IMPLICIT = 0
    CONSTRAINED = 1
    UNCONSTRAINED = 2


class PeriodGenerator:
    def __init__(self,
                 randomValue=None,
                 interval=None,
                 generator=None):
        """
        If using the generator argument, the function being passed should take
        the number of tasks as argument and return that number of RandomValue
        objects in an iterable.

        If using the randomValue argument, that RandomValue will be used to
        generate all periods.

        If using the interval argument, the values will be the extremities of
        that interval plus remaining periods uniformly distributed inside the
        interval.

        :param randomValue:
        :param generator:
        """

        if generator is not None:
            self._gen = generator
        elif interval is not None:
            bot, top = interval

            def gen(nbTasks):
                others = [RandomValue(intrange=(bot, top))
                          for _ in range(nbTasks - 2)]
                return [RandomValue(value=bot), RandomValue(value=top)] + others
            self._gen = gen
        elif randomValue is not None:
            self._gen = lambda x: x * [randomValue]
        else:
            raise AssertionError

    def genPeriodValues(self, nbTasks):
        return self._gen(nbTasks)


class TasksetGenerator:

    def __init__(self, **args):
        """
        The following arguments are available:

        * `periodicity` (a Periodicity value)
        * `scale` (integer)
        * `deadlineCategory` (a DeadlineCategory value)
        * `seed`
        * `periodGenerator` (a PeriodGenerator object)

        The following arguments must be passed as RandomValue instances, if
        present:

        * `utilization`
        * `nbTasks`
        * `preemptionCost`
        """
        self._args = args
        try:
            seed = self._args['seed']
        except KeyError:
            pass
        else:
            random.seed(seed)
        self._randState = random.getstate()

    def __call__(self):
        taskset = None
        while taskset is None:
            builder = _TasksetBuilder(self)
            taskset = builder()
        return taskset

    def periodicity(self):
        return self._args.setdefault('periodicity', Periodicity.PERIODIC)

    def nbTasks(self):
        randNumber = self._args.setdefault('nbTasks', RandomValue(value=1))
        return self._getSeededRandomValue(randNumber)

    def utilization(self):
        randNumber = self._args.setdefault('utilization', RandomValue(value=1))
        return self._getSeededRandomValue(randNumber)

    def periods(self, nbTasks):
        periodGenerator = self._args.setdefault(
            'periodGenerator',
            PeriodGenerator(randomValue=RandomValue(value=1)))
        randPeriods = periodGenerator.genPeriodValues(nbTasks)
        return [self._getSeededRandomValue(r) for r in randPeriods]

    def preemptionCost(self):
        defaultPC = RandomValue(value=FixedPreemptionCost(0))
        randNumber = self._args.setdefault('preemptionCost',
                                           defaultPC)
        return self._getSeededRandomValue(randNumber)

    def scale(self):
        return self._args.setdefault('scale', DEFAULT_SCALE)

    def deadlineCategory(self):
        return self._args.setdefault('deadlineCategory',
                                     DeadlineCategory.IMPLICIT)

    def _getSeededRandomValue(self, randNumber):
        random.setstate(self._randState)
        res = randNumber()
        self._randState = random.getstate()
        return res


class _TasksetBuilder:

    def __init__(self, generator):
        self._generator = generator
        self._nbTasks = generator.nbTasks()
        self._utilization = generator.utilization()
        logger.debug('Creating task set with %s tasks and load %s',
                     self._nbTasks,
                     self._utilization)

    def __call__(self):
        utils = self._genUtils()
        logger.debug('Utils %s', utils)
        periods = list(self._genPeriods())
        logger.debug('Periods %s', periods)
        wcets = self._genWcets(utils, periods)
        logger.debug('Wcets %s', wcets)
        deadlines = list(self._genDeadlines(periods))
        logger.debug('Deadlines %s', deadlines)
        preemptionCosts = list(self._genPCs())
        logger.debug('Preemption costs %s', preemptionCosts)
        arrivalDistribs = self._genArrivalDistribs(periods)
        tasks = list(self._genTasks(wcets,
                                    deadlines,
                                    arrivalDistribs,
                                    preemptionCosts))
        taskset = Taskset(*tasks)
        if taskset.utilization <= self._utilization:
            return taskset
        else:
            return None

    @staticmethod
    def _genTasks(wcets, deadlines, arrivalDistribs, preemptionCosts):
        taskId = 0
        for args in zip(wcets, deadlines, arrivalDistribs, preemptionCosts):
            task = Task(*args, uniqueId=taskId)
            taskId += 1
            yield task

    def _genDeadlines(self, periods):
        if self._generator.deadlineCategory() == DeadlineCategory.IMPLICIT:
            for p in periods:
                yield p
        else:
            raise NotImplemented

    def _genArrivalDistribs(self, periods):
        if self._generator.periodicity() == Periodicity.PERIODIC:
            for p in periods:
                yield FixedArrivalDistribution(p)
        else:
            raise NotImplemented

    def _scale(self):
        return self._generator.scale()

    def _randUPoint(self):
        return random.uniform(0, self._utilization)

    def _genPCs(self):
        for _ in range(self._nbTasks):
            yield self._generator.preemptionCost()

    def _genPeriods(self):
        for period in self._generator.periods(self._nbTasks):
            yield int(math.floor(period * self._scale()))

    @staticmethod
    def _genWcets(utils, periods):
        tupleSeq = [(u, p) for u, p in zip(utils, periods)]
        wcets = [max(1, int(math.floor(u * p))) for u, p in tupleSeq]
        return [int(e) for e in wcets]

    def _genUtils(self):
        points = [1] * (self._nbTasks - 1)
        uPoints = [0, self._utilization] + [self._randUPoint() for _ in points]
        sortedUPoints = sorted(uPoints)
        tupleSeq = zip(sortedUPoints[:-1], sortedUPoints[1:])
        utils = [p2 - p1 for p1, p2 in tupleSeq]
        try:
            assert all(u > 0 for u in utils)
        except AssertionError:
            logger.exception(
                'Generated a negative utilization: {}'.format(utils))
            raise
        return utils
