import re
import os.path as ospath

from .model import Task, Taskset
from .sim import SimulationSetup
from .policy import DualPriorityTaskInfo, DualPrioritySchedulingPolicy


class _SetupFile:
    def __init__(self):
        super().__init__()


class SetupInputFile(_SetupFile):
    REGEX = (r'([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+'
             '([-]?[0-9]+)\s+([0-9]+)\s+([-]?[0-9]+)')

    def __init__(self, path):
        super().__init__()
        self._path = ospath.expandvars(path)

    def lazyRead(self):
        file = open(self._path)
        return self._genSetups(file)

    @staticmethod
    def _buildTask(c, t, d, s, p1, p2):
        assert t == d
        task = Task(int(c), int(d))
        assert p1 >= p2
        if p1 == p2:
            dualPriorityInfo = DualPriorityTaskInfo(int(p1))
        else:
            dualPriorityInfo = DualPriorityTaskInfo(int(p1),
                                                    int(s),
                                                    int(p2))
        return task, dualPriorityInfo

    def _genTasks(self, file):
        line = file.readline()
        while line:
            m = re.match(SetupInputFile.REGEX, line)
            if not m:
                break
            else:
                yield self._buildTask(*m.groups())
                line = file.readline()

    def _genSetups(self, file):
        while file:
            pairs = list(self._genTasks(file))
            if not pairs:
                break
            tasks, dInfos = zip(*pairs)
            taskset = Taskset(*tasks)
            policy = DualPrioritySchedulingPolicy(*pairs)
            setup = SimulationSetup(taskset,
                                    taskset.hyperperiod,
                                    schedulingPolicy=policy)
            yield setup


