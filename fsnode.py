from operator import attrgetter
import posixpath as osp

class Node:
    def __init__(self, parent, name, output=None):
        self.parent   = parent
        self.name     = name
        self.output   = output
        self._children = set()

    def add_child(self, child):
        self._children.add(child)

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

        return reversed(ancestors)

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
