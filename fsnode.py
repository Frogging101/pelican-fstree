import copy
from operator import attrgetter
import posixpath as osp

from .utils import split_path

class Node:
    def __init__(self, parent, name, output=None):
        self.parent   = parent
        self.name     = name
        self.output   = output
        self._children = set()

    def add_child(self, child):
        self._children.add(child)

    def del_child(self, child):
        self._children.remove(child)

    @property
    def children(self):
        return sorted(self._children, key=attrgetter('name'))

    @property
    def ancestors(self):
        ancestors = []
        next = self
        while next.parent is not None:
            ancestors.append(next.parent)
            next = next.parent

        ancestors.reverse()
        return ancestors

    @property
    def level(self):
        if not self.parent:
            return (self,)

        return self.parent.children

    @property
    def path(self):
        path = '/'
        if not self.parent:
            return path
        for a in self.ancestors:
            path = osp.join(path, a.name)
        path = osp.join(path, self.name)
        if len(self.children):
            path = osp.join(path, '')
        return path

    @property
    def ts(self):
        return "timestamp"

    def get_node_at(self, path):
        if self.path == path:
            return self
        for child in self.children:
            ret = child.get_node_at(path)
            if ret is not None:
                return ret

        return None

    def __deepcopy__(self, memo):
        if id(self) in memo:
            return memo[id(self)]
        new = copy.copy(self)
        memo[id(self)] = new
        if new.parent is not None:
            new.parent = copy.deepcopy(new.parent, memo)
        newchildren = set()
        for child in new._children:
            newchild = copy.deepcopy(child, memo)
            newchildren.add(newchild)
        new._children = newchildren

        return new

class NodePrecursor:
    def __init__(self, path, output=None):
        self.path = path
        self.output = output
        self.components = split_path(path)
        self.name = self.components[-1]
