
import logging
import random

from crpd.model import Taskset, Task, FixedArrivalDistribution
from crpd.gen import RandomValue, TasksetGenerator, DEFAULT_SCALE


def test_nonZeroWcet():
    g = TasksetGenerator(seed=1337,
                         scale=10,
                         nbTasks=RandomValue(value=5),
                         period=RandomValue(logRange=(10, 1000)))
    for _ in range(15):
        g()


def test_randomNumber():
    r = RandomValue(value=4)
    assert(r() == 4)


def test_randomNumberRange():
    random.seed(42)
    r = RandomValue(intrange=(0, 1337))
    assert(r() == 1309)
    assert(r() == 228)


def test_randomNumberFloatRange():
    random.seed(42)
    r = RandomValue(floatrange=(1455.000000000099, 82000.17))
    assert(-0.000001 < (r() - 52957.74018434602) < 0.000001)
    assert(-0.000001 < (r() - 3469.4955312381926) < 0.000001)


def test_defaultTaskset():
    g = TasksetGenerator()
    taskset = g()
    expectedTask = Task(DEFAULT_SCALE,
                        DEFAULT_SCALE,
                        FixedArrivalDistribution(DEFAULT_SCALE),
                        uniqueId=0)
    expected = Taskset(expectedTask)
    logging.debug('%s', expected)
    logging.debug('%s', taskset)
    assert(expected == taskset)


def test_seedTaskset():
    g = TasksetGenerator(seed=1337,
                         utilization=RandomValue(floatrange=(0.5, 1)),
                         period=RandomValue(intrange=(1, 100)))
    taskset = g()
    expectedTask = Task(808,
                        1000,
                        uniqueId=0)
    expected = Taskset(expectedTask)
    assert(expected == taskset)


def test_twoIntertwinedGens():
    g1 = TasksetGenerator(seed=1337,
                          utilization=RandomValue(floatrange=(0.5, 1)),
                          period=RandomValue(intrange=(1, 100)))
    g2 = TasksetGenerator(seed=42,
                          utilization=RandomValue(floatrange=(0.5, 1)),
                          period=RandomValue(intrange=(1, 100)))
    taskset1 = g1()
    taskset2 = g2()
    taskset3 = g1()
    expectedTask1 = Task(808,
                         1000,
                         uniqueId=0)
    expected1 = Taskset(expectedTask1)
    expectedTask2 = Task(819,
                         1000,
                         uniqueId=0)
    expected2 = Taskset(expectedTask2)
    expectedTask3 = Task(766,
                         1000,
                         uniqueId=0)
    expected3 = Taskset(expectedTask3)
    assert(expected1 == taskset1)
    assert(expected2 == taskset2)
    assert(expected3 == taskset3)
