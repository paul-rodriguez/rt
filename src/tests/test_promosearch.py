import pytest

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


def assertRMm1RM(taskset, success=True):
    raised = False
    try:
        policy = dichotomicPromotionSearch(taskset)
        if success:
            setup = SimulationSetup(taskset,
                                    taskset.hyperperiod,
                                    schedulingPolicy=policy,
                                    deadlineMissFilter=True)
            result = SimulationRun(setup).result()
            history = result.history
            assert not history.hasDeadlineMiss()
    except ValidPromotionNotFound:
        raised = True
    assert not raised if success else raised


def assertGDF(taskset, success=True):
    policy = greedyDeadlineFixPolicy(taskset)
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


@pytest.mark.slow
def test_RMm1RMsuccess01():
    taskset = Taskset(Task(1, 40),
                      Task(9, 107),
                      Task(1, 54),
                      Task(43, 60),
                      Task(7, 51))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess02():
    taskset = Taskset(Task(1, 40),
                      Task(16, 91),
                      Task(27, 75),
                      Task(17, 55),
                      Task(6, 50))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMsuccess03():
    taskset = Taskset(Task(1, 40),
                      Task(16, 112),
                      Task(7, 60),
                      Task(35, 100),
                      Task(27, 75))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMsuccess04():
    taskset = Taskset(Task(1, 40),
                      Task(16, 92),
                      Task(27, 75),
                      Task(17, 55),
                      Task(6, 50))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMsuccess05():
    taskset = Taskset(Task(1, 40),
                      Task(17, 119),
                      Task(7, 60),
                      Task(35, 100),
                      Task(27, 75))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess06():
    taskset = Taskset(Task(1, 40),
                      Task(12, 109),
                      Task(1, 104),
                      Task(29, 78),
                      Task(24, 56),
                      Task(2, 40))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess07():
    taskset = Taskset(Task(12, 40),
                      Task(1, 103),
                      Task(13, 100),
                      Task(1, 81),
                      Task(31, 60))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess08():
    taskset = Taskset(Task(16, 40),
                      Task(16, 101),
                      Task(1, 60),
                      Task(15, 76),
                      Task(8, 40),
                      Task(1, 66))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess09():
    taskset = Taskset(Task(1, 40),
                      Task(7, 97),
                      Task(1, 45),
                      Task(20, 53),
                      Task(20, 40))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess10():
    taskset = Taskset(Task(1, 40),
                      Task(17, 106),
                      Task(29, 62),
                      Task(33, 96))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMsuccess11():
    taskset = Taskset(Task(11, 40),
                      Task(14, 82),
                      Task(31, 58))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMsuccess12():
    taskset = Taskset(Task(1, 40),
                      Task(11, 64),
                      Task(1, 46),
                      Task(4, 42),
                      Task(10, 46),
                      Task(28, 60))
    assertRMm1RM(taskset, success=True)


@pytest.mark.slow
def test_RMm1RMsuccess13():
    taskset = Taskset(Task(1, 40),
                      Task(12, 101),
                      Task(16, 48),
                      Task(37, 73))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMsuccess14():
    taskset = Taskset(Task(13, 51),
                      Task(83, 128),
                      Task(16, 183))
    assertRMm1RM(taskset, success=True)


def test_RMm1RMfailure01():
    taskset = Taskset(Task(1, 40),
                      Task(5, 114),
                      Task(18, 93),
                      Task(7, 47),
                      Task(42, 72))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure02():
    taskset = Taskset(Task(1, 40),
                      Task(7, 115),
                      Task(18, 79),
                      Task(28, 41))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure03():
    taskset = Taskset(Task(1, 40),
                      Task(7, 116),
                      Task(18, 79),
                      Task(28, 41))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure04():
    taskset = Taskset(Task(21, 40),
                      Task(1, 58),
                      Task(25, 57))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure05():
    taskset = Taskset(Task(9, 40),
                      Task(9, 74),
                      Task(35, 54))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure06():
    taskset = Taskset(Task(14, 40),
                      Task(9, 81),
                      Task(1, 70),
                      Task(36, 69))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure07():
    taskset = Taskset(Task(1, 40),
                      Task(10, 100),
                      Task(11, 46),
                      Task(35, 56))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure08():
    taskset = Taskset(Task(1, 40),
                      Task(10, 99),
                      Task(11, 46),
                      Task(35, 56))
    assertRMm1RM(taskset, success=False)


def test_RMm1RMfailure09():
    taskset = Taskset(Task(3, 40),
                      Task(1, 102),
                      Task(32, 56),
                      Task(27, 82),
                      Task(1, 85))
    assertRMm1RM(taskset, success=False)


def test_GDFsuccess01():
    taskset = Taskset(Task(21, 40),
                      Task(1, 58),
                      Task(25, 57))
    assertGDF(taskset, success=True)


@pytest.mark.slow
def test_GDFsuccess02():
    taskset = Taskset(Task(1, 40),
                      Task(12, 101),
                      Task(16, 48),
                      Task(37, 73))
    assertGDF(taskset, success=True)


@pytest.mark.slow
def test_GDFsuccess03():
    taskset = Taskset(Task(1, 40),
                      Task(9, 107),
                      Task(1, 54),
                      Task(43, 60),
                      Task(7, 51))
    assertGDF(taskset, success=True)


def test_GDFsuccess04():
    taskset = Taskset(Task(1, 40),
                      Task(17, 119),
                      Task(7, 60),
                      Task(35, 100),
                      Task(27, 75))
    assertGDF(taskset, success=True)


def test_GDFsuccess05():
    taskset = Taskset(Task(1, 40),
                      Task(16, 92),
                      Task(27, 75),
                      Task(17, 55),
                      Task(6, 50))
    assertGDF(taskset, success=True)


def test_GDFsuccess06():
    taskset = Taskset(Task(1, 40),
                      Task(16, 112),
                      Task(7, 60),
                      Task(35, 100),
                      Task(27, 75))
    assertGDF(taskset, success=True)


def test_GDFsuccess07():
    taskset = Taskset(Task(9, 40),
                      Task(9, 74),
                      Task(35, 54))
    assertGDF(taskset, success=True)


@pytest.mark.slow
def test_GDFsuccess08():
    taskset = Taskset(Task(1, 40),
                      Task(17, 106),
                      Task(29, 62),
                      Task(33, 96))
    assertGDF(taskset, success=True)


@pytest.mark.slow
def test_GDFsuccess09():
    taskset = Taskset(Task(1, 40),
                      Task(16, 91),
                      Task(27, 75),
                      Task(17, 55),
                      Task(6, 50))
    assertGDF(taskset, success=True)


def test_GDFsuccess10():
    taskset = Taskset(Task(11, 40),
                      Task(14, 82),
                      Task(31, 58))
    assertGDF(taskset, success=True)
