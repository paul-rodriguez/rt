from crpd.model import Task, Taskset
from crpd.sim import SimulationRun, SimulationSetup
from dualpriority.policies import (
    ValidPromotionNotFound,
    rmLaxityPromotions,
    dichotomicPromotionSearch,
    dajamPromotions,
    genLpViableTasks,
    greedyDeadlineFixPolicy,
)


def assertRML(taskset, success=True, lpvPrep=True):
    policy = rmLaxityPromotions(taskset, lpvPrep=lpvPrep)
    setup = SimulationSetup(taskset,
                            taskset.hyperperiod,
                            schedulingPolicy=policy,
                            deadlineMissFilter=True)
    result = SimulationRun(setup).result()
    history = result.history
    if success:
        assert not history.hasDeadlineMiss()
    else:
        assert history.hasDeadlineMiss()


def test_RMLfailure01():
    taskset = Taskset(Task(6, 13),
                      Task(8, 18),
                      Task(6, 86))
    assertRML(taskset, success=False)


def test_RMLfailure02():
    taskset = Taskset(Task(8, 20),
                      Task(15, 28),
                      Task(8, 136))
    assertRML(taskset, success=False)


def test_RMLfailure21():
    taskset = Taskset(Task(7, 24),
                      Task(22, 36),
                      Task(4, 50))
    assertRML(taskset, success=False)


def test_RMLfailure22():
    taskset = Taskset(Task(23, 40),
                      Task(23, 58),
                      Task(1, 60))
    assertRML(taskset, success=False)


def test_RMLfailure03():
    taskset = Taskset(Task(13, 51),
                      Task(83, 128),
                      Task(16, 183))
    assertRML(taskset, success=False)


def test_RMLfailure04():
    taskset = Taskset(Task(22, 87),
                      Task(131, 237),
                      Task(53, 280))
    assertRML(taskset, success=False)


def test_RMLfailure05():
    taskset = Taskset(Task(1, 40),
                      Task(28, 41),
                      Task(18, 79),
                      Task(7, 115))
    assertRML(taskset, success=False)


def test_RMLfailure06():
    taskset = Taskset(Task(1, 40),
                      Task(11, 46),
                      Task(35, 56),
                      Task(10, 100))
    assertRML(taskset, success=False)


def test_RMLfailure07():
    taskset = Taskset(Task(1, 40),
                      Task(7, 116),
                      Task(18, 79),
                      Task(28, 41))
    assertRML(taskset, success=False)


def test_RMLfailure08():
    taskset = Taskset(Task(1, 40),
                      Task(10, 99),
                      Task(11, 46),
                      Task(35, 56))
    assertRML(taskset, success=False)


def test_RMLfailure09():
    taskset = Taskset(Task(14, 40),
                      Task(9, 81),
                      Task(1, 70),
                      Task(36, 69))
    assertRML(taskset, success=False)


def test_RMLfailure13():
    taskset = Taskset(Task(1, 24),
                      Task(11, 26),
                      Task(16, 39),
                      Task(1, 100),
                      Task(12, 127))
    assertRML(taskset, success=False)


def test_RMLfailure10():
    taskset = Taskset(Task(1, 40),
                      Task(20, 40),
                      Task(1, 45),
                      Task(20, 53),
                      Task(7, 97))
    assertRML(taskset, success=False)


def test_RMLfailure11():
    taskset = Taskset(Task(1, 40),
                      Task(7, 47),
                      Task(42, 72),
                      Task(18, 93),
                      Task(5, 114))
    assertRML(taskset, success=False)


def test_RMLfailure12():
    taskset = Taskset(Task(3, 40),
                      Task(32, 56),
                      Task(27, 82),
                      Task(1, 85),
                      Task(1, 102))
    assertRML(taskset, success=False)


def test_RMLfailure14():
    taskset = Taskset(Task(12, 40),
                      Task(31, 60),
                      Task(1, 81),
                      Task(13, 100),
                      Task(1, 103))
    assertRML(taskset, success=False)


def test_RMLfailure15():
    taskset = Taskset(Task(1, 40),
                      Task(12, 109),
                      Task(1, 104),
                      Task(29, 78),
                      Task(24, 56),
                      Task(2, 40))
    assertRML(taskset, success=False)


def test_RMLfailure16():
    taskset = Taskset(Task(1, 40),
                      Task(11, 64),
                      Task(1, 46),
                      Task(4, 42),
                      Task(10, 46),
                      Task(28, 60))
    assertRML(taskset, success=False)


def test_RMLfailure17():
    taskset = Taskset(Task(16, 40),
                      Task(16, 101),
                      Task(1, 60),
                      Task(15, 76),
                      Task(8, 40),
                      Task(1, 66))
    assertRML(taskset, success=False)


def test_RMLfailure18():
    taskset = Taskset(Task(1, 40),
                      Task(17, 104),
                      Task(3, 61),
                      Task(29, 68),
                      Task(3, 52),
                      Task(11, 40))
    assertRML(taskset, success=False)


def test_RMLfailure19():
    taskset = Taskset(Task(1, 40),
                      Task(11, 64),
                      Task(1, 46),
                      Task(4, 42),
                      Task(10, 46),
                      Task(28, 60))
    assertRML(taskset, success=False)


def test_RMLfailure20():
    taskset = Taskset(Task(16, 40),
                      Task(16, 101),
                      Task(1, 60),
                      Task(15, 76),
                      Task(8, 40),
                      Task(1, 66))
    assertRML(taskset, success=False)


def test_RMLsuccess01():
    taskset = Taskset(Task(1, 5),
                      Task(6, 39),
                      Task(16, 39))
    assertRML(taskset, success=True)


def test_RMLsuccess02():
    taskset = Taskset(Task(3, 6),
                      Task(4, 9),
                      Task(1, 18))
    assertRML(taskset, success=True)


def test_RMLsuccess03():
    taskset = Taskset(Task(3, 6),
                      Task(4, 9),
                      Task(2, 36))
    assertRML(taskset, success=True)


def test_RMLsuccess04():
    taskset = Taskset(Task(5, 18),
                      Task(16, 24),
                      Task(1, 25))
    assertRML(taskset, success=True)


def test_RMLsuccess05():
    taskset = Taskset(Task(8, 42),
                      Task(38, 51),
                      Task(1, 52))
    assertRML(taskset, success=True)


def test_RMLsuccess06():
    taskset = Taskset(Task(1, 4),
                      Task(2, 15),
                      Task(14, 23),
                      Task(1, 1380))
    assertRML(taskset, success=True)


def test_RMLsuccess07():
    taskset = Taskset(Task(1, 40),
                      Task(9, 82),
                      Task(1, 48),
                      Task(18, 48))
    assertRML(taskset, success=True)


def test_RMLnoPrepfailure01():
    taskset = Taskset(Task(3, 6),
                      Task(4, 9),
                      Task(2, 36))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure03():
    taskset = Taskset(Task(21, 40),
                      Task(25, 57),
                      Task(1, 58))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure04():
    taskset = Taskset(Task(11, 40),
                      Task(31, 58),
                      Task(14, 82))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure05():
    taskset = Taskset(Task(9, 40),
                      Task(35, 54),
                      Task(9, 74))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure06():
    taskset = Taskset(Task(1, 40),
                      Task(16, 48),
                      Task(37, 73),
                      Task(12, 101))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure07():
    taskset = Taskset(Task(1, 40),
                      Task(29, 62),
                      Task(33, 96),
                      Task(17, 106))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure08():
    taskset = Taskset(Task(1, 24),
                      Task(11, 26),
                      Task(16, 39),
                      Task(1, 100),
                      Task(12, 127))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure13():
    taskset = Taskset(Task(1, 40),
                      Task(6, 50),
                      Task(17, 55),
                      Task(27, 75),
                      Task(16, 91))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure09():
    taskset = Taskset(Task(1, 40),
                      Task(6, 50),
                      Task(17, 55),
                      Task(27, 75),
                      Task(16, 92))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure10():
    taskset = Taskset(Task(1, 40),
                      Task(7, 51),
                      Task(1, 54),
                      Task(43, 60),
                      Task(9, 107))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure11():
    taskset = Taskset(Task(1, 40),
                      Task(7, 60),
                      Task(27, 75),
                      Task(35, 100),
                      Task(16, 112))
    assertRML(taskset, success=False, lpvPrep=False)


def test_RMLnoPrepfailure12():
    taskset = Taskset(Task(1, 40),
                      Task(7, 60),
                      Task(27, 75),
                      Task(35, 100),
                      Task(17, 119))
    assertRML(taskset, success=False, lpvPrep=False)
