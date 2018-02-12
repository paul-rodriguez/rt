class _HistoryMap:

    def __init__(self, *argSet):
        self._maps = {a: {} for a in argSet}
        self._all = set()

    def lookup(self, **args):
        cuts = []

        for key, argval in args.items():
            mapForKey = self._maps[key]
            cut = mapForKey.get(argval, set())
            cuts.append(cut)

        if len(cuts) > 0:
            res = set(cuts[0])
            for c in cuts[1:]:
                res = res & c
            return res
        else:
            return self._all

    def _addItem(self, item, **args):
        for key, argval in args.items():
            mapForKey = self._maps[key]
            try:
                mapForKey[argval].add(item)
            except KeyError:
                mapForKey[argval] = {item}
            self._all.add(item)


class DeadlineMissMap(_HistoryMap):

    def __init__(self):
        super().__init__('time', 'task')

    def addState(self, state):
        for deadlineMiss in state.deadlineMisses:
            self._addItem(deadlineMiss,
                          time=deadlineMiss.time,
                          task=deadlineMiss.task)

    def firstOccurrence(self, dmFilter):
        allMisses = set(self.lookup())
        while allMisses:
            minDeadlineMiss = min(allMisses, key=lambda x: x.time)
            if dmFilter.match(minDeadlineMiss.task):
                return minDeadlineMiss
            allMisses.remove(minDeadlineMiss)
        return None


class PreemptionMap(_HistoryMap):

    def __init__(self):
        super().__init__('time', 'preemptedTask', 'preemptingTask')

    def addState(self, state):
        for preemption in state.preemptions:
            self._addItem(preemption,
                          time=preemption.time,
                          preemptedTask=preemption.preemptedTask,
                          preemptingTask=preemption.preemptingTask)
