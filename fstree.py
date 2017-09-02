from collections import namedtuple
import posixpath as osp
from functools import partial

from pelican import signals
from pelican.utils import posixize_path
from pelican.outputs import HTMLOutput

from .fsnode import Node
from .render_tree import render_tree

def split_path(path, components=None):
    if components is None:
        components = []
    path = osp.normpath(path)
    head, tail = osp.split(path)
    if not head or not tail:
        if head:
            components.insert(0, head)
        if tail:
            components.insert(0, tail)
        return components

    components.insert(0, tail)
    return split_path(head, components)

def normalize_path(path):
    path = posixize_path(osp.normpath(path))
    if not osp.isabs(path):
        path = osp.join('/', path)
    if osp.basename(path) == "index.html":
        path = osp.dirname(path)

    return path

def add_nodes(generators, outputs):
    PO = namedtuple('PO', ['path', 'output'])
    paths_outputs = [PO(normalize_path(o.path), o) for o in outputs if
                     type(o) is HTMLOutput]

    paths = [po.path for po in paths_outputs]
    try:
        assert len(paths) == len(set(paths)), "we got dupes"
    except AssertionError as e:
        e.args += (paths,)
        raise

    splitpaths = [PO(split_path(po.path), po.output) for po in paths_outputs]
    splitpaths.sort(key=lambda item: len(item.path))
    
    root = Node(None, splitpaths[0].path[-1])
    splitpaths[0].output.template_vars['node'] = root
    root.output = splitpaths[0].output
    root.render_tree = partial(render_tree, root)
    
    nodes = [[(splitpaths[0].path, root)]]
    splitpaths.pop(0)
    for po in splitpaths:
        components = po.path
        output = po.output
        depth = len(components)-1

        if len(nodes) <= depth:
            nodes.append([])

        parent = None
        for p in nodes[depth-1]:
            if p[0] == components[:-1]:
                parent = p[1]

        try:
            assert parent
        except AssertionError as e:
            e.args += (depth, components, nodes[depth-1])
            raise
        node = Node(parent, components[-1])
        parent.add_child(node)
        output.template_vars['node'] = node
        node.output = output
        node.render_tree = partial(render_tree, node)
        nodes[depth].append((components, node))

def register():
    signals.all_generators_finalized.connect(add_nodes)
