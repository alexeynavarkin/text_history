from abc import ABC, abstractmethod
from math import inf


class TextHistory:
    def __init__(self, text='', actions=None, version=0):
        self._actions = [] if not actions else actions
        self._text = text
        self._version = version

    def __str__(self):
        return "TextHistory(ver.{}):\n{}".format(self._version, self._text)

    @property
    def text(self):
        return self._text

    @property
    def version(self):
        return self._version

    def action(self, act):
        if act.from_version != self._version:
            raise ValueError("Action version differs from current text version.")
        self._text = act.apply(self._text)
        self._actions.append(act)
        self._version = act.to_version
        return act.to_version

    def insert(self, text, pos=None):
        if pos is None:
            pos = len(self._text)
        act = InsertAction(text, pos, self._version, self._version+1)
        return self.action(act)

    def delete(self, pos, length):
        act = DeleteAction(pos, length, self._version, self._version+1)
        return self.action(act)

    def replace(self, text, pos=None):
        if pos is None:
            pos = len(self._text)
        act = ReplaceAction(text, pos, self._version, self._version+1)
        return self.action(act)

    def optimize(self, actions):
        idx = 0
        while idx < len(actions)-1:
            # some cool variables
            f_act = actions[idx]
            s_act = actions[idx+1]
            if f_act.merge(s_act):
                actions.pop(idx+1)
            idx += 1
        return actions

    def get_actions(self, from_version=None, to_version=None):
        if from_version is None:
            from_version = 0
        if to_version is None:
            to_version = inf
        if from_version < 0 or to_version < 0:
            raise ValueError("Versions can not be negative.")
        if from_version > to_version:
            raise ValueError("Bad version range. (from_version < to_version)")
        if to_version != inf and to_version > self._actions[-1].to_version:
            raise ValueError("Given version out of range.")
        actions = []
        for action in self._actions:
            if action.from_version >= from_version and action.to_version <= to_version:
                actions.append(action)
        return self.optimize(actions)


class Action(ABC):
    """
    Abstract action class for text editing

    Attributes:
        _from_version - from that version action can update text
        _to_version   - to that version action can update text
    """
    def __init__(self, from_version, to_version):
        if from_version >= to_version or from_version < 0 or to_version < 0:
            raise ValueError("Wrong version values.")
        self._from_version = from_version
        self._to_version = to_version

    @property
    def from_version(self):
        return self._from_version

    @property
    def to_version(self):
        return self._to_version

    @abstractmethod
    def apply(self, apply_to):
        pass


class InsertAction(Action):
    """
    Class for insert action

    Attributes:
        _text - text that should be inserted
        _pos  - position where _text should be inserted
    """
    def __init__(self,  text, pos, from_version, to_version):
        if pos is not None and int(pos) < 0:
            raise ValueError("Pos can not be negative.")
        self._text = text
        self._pos = pos
        super().__init__(from_version, to_version)

    def __repr__(self):
        return "InsertAction(text={}, pos='{}', from_version={}, to_version={})" \
               .format(self._text, self._pos, self._from_version, self._to_version)

    @property
    def text(self):
        return self._text

    @property
    def pos(self):
        return self._pos

    def merge(self, action):
        return action.merge_with_insert(self)

    def merge_with_replace(self, action):
        return None

    def merge_with_delete(self, action):
        return None

    def merge_with_insert(self, action):
        return None

    def apply(self, apply_to):
        if len(apply_to) < self._pos:
            raise ValueError("Insert position {} out of string length {}." \
                             .format(self._pos, len(apply_to)))
        return apply_to[:self._pos] + self._text + apply_to[self._pos:]


class DeleteAction(Action):
    """
        Class for insert action

        Attributes:
            _pos    - position from where to delete
            _length - length to delete
        """
    def __init__(self,  pos, length, from_version, to_version):
        if pos < 0 or length < 0:
            raise ValueError("Pos and length can not be negative.")
        self._pos = pos
        self._length = length
        super().__init__(from_version, to_version)

    def __repr__(self):
        return "DeleteAction(pos={}, length={}, from_version={}, to_version={})" \
               .format(self._pos, self._length, self._from_version, self._to_version)

    def __eq__(self, other):
        if isinstance(other, DeleteAction) and self._pos == other._pos:
            return True
        return False

    @property
    def pos(self):
        return self._pos

    @property
    def length(self):
        return self._length

    def merge(self, action):
        return action.merge_with_delete(self)

    def merge_with_replace(self, action):
        return None

    def merge_with_delete(self, action):
        if self._pos == action._pos:
            action._length += self._length
            if action._from_version < self._from_version:
                action._to_version = self._to_version
            else:
                action._from_version = self._from_version
            return True
        return None

    def merge_with_insert(self, action):
        return None

    def apply(self, apply_to):
        if int(self._pos) > len(apply_to):
            raise ValueError("Pos out of string length.")
        if self._pos + self._length > len(apply_to):
            raise ValueError("Trying to delete symbols out of string.")
        return apply_to[:self._pos] + apply_to[self._pos+self._length:]


class ReplaceAction(Action):
    """
        Class for insert action

        Attributes:
            _text - text to use as replacement
            _pos  - position from where to replace
    """
    def __init__(self, text, pos, from_version, to_version):
        if pos is not None and pos < 0:
            raise ValueError("Pos can not be negative.")
        self._text = text
        self._pos = pos
        super().__init__(from_version, to_version)

    def __repr__(self):
        return "ReplaceAction(text='{}', pos={}, from_version={}, to_version={})" \
               .format(self._text, self._pos, self._from_version, self._to_version)

    def __eq__(self, other):
        if isinstance(other, ReplaceAction) and self._pos == other._pos:
            return True
        return False

    @property
    def text(self):
        return self._text

    @property
    def pos(self):
        return self._pos

    def merge(self, action):
        return action.merge_with_replace(self)

    def merge_with_replace(self, action):
        if self._pos == action._pos and len(self._text) >= len(action._text):
            if action._to_version < self._to_version:
                action._to_version = self._to_version
                action._text = self._text
            else:
                action._from_version = self._from_version
            return True
        return None

    def merge_with_delete(self, action):
        return None

    def merge_with_insert(self, action):
        return None

    def apply(self, apply_to):
        if len(apply_to) < self._pos:
            raise ValueError("Insert position {} out of string length {}." \
                             .format(self._pos, len(apply_to)))
        return apply_to[:self._pos] + self._text + apply_to[self._pos+len(self._text):]
