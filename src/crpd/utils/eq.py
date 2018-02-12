
import logging

logger = logging.getLogger(__name__)


class ValueEqual:
    """
    Inheriting from this class makes the child compare itself by value instead
    of identity.

    Subclasses can exclude certain fields from comparison by redefining the
    _nonValueFields() method.
    All the included fields must be immutable.
    """

    def __init__(self):
        self._hash = None

    def _nonValueFields(self):
        """
        Redefine this function in children classes to change the scope of the
        equality.
        """
        return tuple()

    def eqData(self):
        allFields = self.__dict__.keys()
        exclude = set(self._nonValueFields() + ('_hash',))
        equalityKeys = allFields - exclude
        result = frozenset((k, self.__dict__[k]) for k in equalityKeys)
        return result

    def __eq__(self, other):
        if self is other:
            return True
        elif self.__class__ is not other.__class__:
            return False
        elif hash(self) != hash(other):
            return False
        else:
            return self.eqData() == other.eqData()

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        if self._hash is None:
            try:
                self._hash = hash(self.eqData())
            except TypeError:
                raise
        return self._hash

    def __getstate__(self):
        stateDict = {k: v for k, v in self.__dict__.items() if k != '_hash'}
        return stateDict

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._hash = None
