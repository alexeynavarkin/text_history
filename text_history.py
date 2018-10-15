from abc import ABC, abstractmethod


class TextHistory:
    def __init__(self, text='', actions=None, version=0):
        self._actions = [] if not actions else actions
        self._text = text
        self._version = version

    def __str__(self):
        return "TextHistory: (ver.{})".format(self._version)

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
        # TODO: maybe keep replaced fragment to revert
        act = InsertAction(text, pos, self._version, self._version+1)
        return self.action(act)

    def delete(self, pos, length):
        # TODO: maybe keep deleted fragment to revert
        act = DeleteAction(pos, length, self._version, self._version+1)
        return self.action(act)

    def replace(self, text, pos=None):
        act = ReplaceAction(text, pos, self._version, self._version+1)
        return self.action(act)

    def get_actions(self, from_versionsion, to_versionsion):
        # TODO: implement function
        pass


class Action(ABC):
    def __init__(self, from_version, to_version):
        if from_version >= to_version or from_version < 0 or to_version < 0:
            raise ValueError("Wrong version values.")
        self._from_version = from_version
        self._to_version = to_version
        print("Created action from ver. {} to {}"\
              .format(from_version, to_version))

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
    def __init__(self,  text, pos, from_version, to_version):
        if pos is not None and int(pos) < 0:
            raise ValueError("Pos can not be negative.")
        self._text = text
        self._pos = pos
        super().__init__(from_version, to_version)
        print(self)

    def apply(self, apply_to):
        if self._pos is None:
            pos = len(apply_to)
        elif len(apply_to) < self._pos:
            raise ValueError("Insert position {} out of string length {}." \
                             .format(self._pos, len(apply_to)))
        else:
            pos = self._pos
        return apply_to[:pos] + self._text + apply_to[pos:]

    def __str__(self):
        return "Insert Action: pos {} text {}(ver. {}->{})" \
            .format(self._pos, self._text, self._from_version, self._to_version)


class DeleteAction(Action):
    def __init__(self,  pos, length, from_version, to_version):
        if pos < 0 or length < 0:
            raise ValueError("Pos and length can not be negative.")
        self._pos = pos
        self._length = length
        super().__init__(from_version, to_version)

    def apply(self, apply_to):
        if int(self._pos) > len(apply_to):
            raise ValueError("Pos out of string length.")
        if self._pos + self._length > len(apply_to):
            raise ValueError("Trying to delete symbols out of string.")
        return apply_to[:self._pos] + apply_to[self._pos+self._length:]


class ReplaceAction(Action):
    def __init__(self, text, pos, from_version, to_version):
        super().__init__(from_version, to_version)
        if pos is not None and pos < 0:
            raise ValueError("Pos can not be negative.")
        self._text = text
        self._pos = pos

    def apply(self, apply_to):
        if self._pos is None:
            pos = len(apply_to)
        elif len(apply_to) < self._pos:
            raise ValueError("Insert position {} out of string length {}." \
                             .format(self._pos, len(apply_to)))
        else:
            pos = self._pos
        return apply_to[:pos] + self._text + apply_to[pos+len(self._text):]