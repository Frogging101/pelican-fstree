from operator import attrgetter

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
    def ts(self):
        return "timestamp"
