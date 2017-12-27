from collections import namedtuple
import posixpath as osp
from functools import partial

from pelican import signals
from pelican import contents
from pelican.utils import posixize_path
from pelican.outputs import HTMLOutput
from pelican.writers import Writer

from .fsnode import Node
from .render_tree import render_tree, render_tree_ancestors
from .dirlist import DirListGenerator

settings = None
dlgen = None
writer = None

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

"""Initialize a Node with a parent (optional), name, and Output object.

The new Node is added to the parent's list of children, and a reference
to it is stored in the Output object's "node" template variable.
"""
def init_node(parent, name, output):
    node = Node(parent, name, output)
    node.render_tree = partial(render_tree, node, settings)
    node.render_tree_ancestors = partial(render_tree_ancestors, node, settings)
    output.template_vars['node'] = node
    if parent:
        parent.add_child(node)
    return node

"""Creates a Node for each Output object.

Nodes will be stored in the corresponding Output object's "node"
template variable by init_node().
"""
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
    # Sort paths in ascending order of number of components
    splitpaths.sort(key=lambda item: len(item.path))

    # Create root node for Output with first (shortest) path
    root = init_node(None, splitpaths[0].path[-1], splitpaths[0].output)
    nodes = [[(splitpaths[0].path, root)]] # Indexed by depth, nodes[0]
                                           # contains only ('/', root).
    splitpaths.pop(0)

    new_outputs = []
    # Create the rest of the nodes
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

        if not parent:
            # Go up until we find an ancestor that exists
            for level in range(depth-1, -1, -1):
                for p in nodes[level]:
                    if p[0] == components[:level+1]:
                        # Found an ancestor. The nesting is getting a
                        # bit ridiculous, but bear with me. Now we're
                        # going to create a directory listing for each
                        # missing level.
                        _parent = p[1]
                        for missing in range(level+1, depth):
                            _splitpath = components[:missing+1]
                            _path = '/'.join(_splitpath[1:])
                            _output = dlgen.generate_directory_listing(_path)
                            _node = init_node(_parent, _splitpath[-1], _output)
                            nodes[missing].append((_splitpath, _node))
                            new_outputs.append(_output)
                            _parent = _node
                        parent = _parent
                        break
                if parent:
                    break

        try:
            assert parent
        except AssertionError as e:
            e.args += (depth, components, nodes[depth-1])
            raise
        node = init_node(parent, components[-1], output)
        nodes[depth].append((components, node))

    for output in new_outputs:
        writer.write_output(output, dlgen.context)

"""Store source directory (with trailing slash) in
content.metadata['dir'].

Some leading components (such as those in PAGE_PATHS for pages) are
removed.
"""
def add_dir(content):
    global settings
    if content.source_path is None:
        return

    dirname = content.relative_dir
    if type(content) == contents.Page:
        dirname = dirname.replace(osp.commonprefix(
                settings['PAGE_PATHS'] + [dirname,]),
            '')

    if dirname:
        # Remove leading slash
        if osp.isabs(dirname):
            dirname = osp.relpath(dirname, '/')
        # Add trailing slash
        dirname += '/'

    content.metadata['dir'] = dirname

def init(pelican):
    global settings, writer
    settings = pelican.settings
    writer = Writer(pelican.output_path, settings)

def add_dirlist_generator(pelican):
    return DirListGenerator

def get_dirlist_generator(generator):
    global dlgen
    if isinstance(generator, DirListGenerator):
        dlgen = generator

def register():
    signals.initialized.connect(init)
    signals.get_generators.connect(add_dirlist_generator)
    signals.generator_init.connect(get_dirlist_generator)
    signals.all_generators_finalized.connect(add_nodes)
    signals.content_object_init.connect(add_dir)
