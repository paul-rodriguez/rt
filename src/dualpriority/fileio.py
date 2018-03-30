import re
import os.path as ospath

from crpd.model import Task, Taskset
from crpd.sim import SimulationSetup
from crpd.policy import DualPriorityTaskInfo, DualPrioritySchedulingPolicy


class _SetupFile:
    def __init__(self, path):
        super().__init__()
        self._path = ospath.expandvars(path)

    @property
    def path(self):
        return self._path


class DPOutputFile(_SetupFile):

    def __init__(self, path):
        super().__init__(path)

    def write(self, *setups):
        with open(self.path, 'a') as file:
            for setup in setups:
                self._writeTaskset(file,
                                   setup.taskset,
                                   setup.schedulingPolicy)

    def _writeTaskset(self, file, taskset, policy):
        for task in taskset:
            taskInfo = policy.schedulerInfo(task)
            self._writeTask(file, task, taskInfo)
        file.write('\n')

    @staticmethod
    def _writeTask(file, task, taskInfo):
        if taskInfo.hasPromotion:
            promotion = taskInfo.promotion
            highPriority = taskInfo.highPriority
        else:
            promotion = task.minimalInterArrivalTime
            highPriority = taskInfo.lowPriority
        taskStr = '{} {} {} {} {} {}\n'.format(task.wcet,
                                               task.minimalInterArrivalTime,
                                               task.minimalInterArrivalTime,
                                               promotion,
                                               taskInfo.lowPriority,
                                               highPriority)
        file.write(taskStr)


class DPInputFile(_SetupFile):
    REGEX = (r'([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+'
             '([-]?[0-9]+)\s+([0-9]+)\s+([-]?[0-9]+)')

    def __init__(self, path):
        super().__init__(path)

    def lazyRead(self):
        file = open(self.path)
        return self._genSetups(file)

    def eagerRead(self):
        return list(self.lazyRead())

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
            m = re.match(self.__class__.REGEX, line)
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


