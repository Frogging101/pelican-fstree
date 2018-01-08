import posixpath as osp
from functools import partial

from pelican import signals
from pelican import contents
from pelican.utils import posixize_path
from pelican.outputs import HTMLOutput
from pelican.writers import Writer

from .fsnode import Node, NodePrecursor as NP
from .render_tree import render_tree, render_tree_ancestors
from .dirlist import DirListGenerator
from .utils import split_path

settings = None
dlgen = None
writer = None

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
    precursors = [NP(normalize_path(o.path), o) for o in outputs if
                  type(o) is HTMLOutput]

    paths = [p.path for p in precursors]
    try:
        assert len(paths) == len(set(paths)), "we got dupes"
    except AssertionError as e:
        e.args += (paths,)
        raise

    # Sort precursors in ascending order of number of path components
    precursors.sort(key=lambda item: len(item.components))

    # Create root node for precursor with first (shortest) path
    root = init_node(None, precursors[0].name, precursors[0].output)
    nodes = [[(precursors[0].components, root)]] # Indexed by depth, nodes[0]
                                                 # contains only ('/', root).
    precursors.pop(0)

    new_outputs = []
    # Create the rest of the nodes
    for precursor in precursors:
        output = precursor.output
        depth = len(precursor.components)-1

        if len(nodes) <= depth:
            nodes.append([])

        parent = None
        for p in nodes[depth-1]:
            if p[0] == precursor.components[:-1]:
                parent = p[1]

        if not parent:
            # Go up until we find an ancestor that exists
            for level in range(depth-1, -1, -1):
                for p in nodes[level]:
                    if p[0] == precursor.components[:level+1]:
                        # Found an ancestor. The nesting is getting a
                        # bit ridiculous, but bear with me. Now we're
                        # going to create a directory listing for each
                        # missing level.
                        _parent = p[1]
                        for missing in range(level+1, depth):
                            _components = precursor.components[:missing+1]
                            _path = '/'.join(_components[1:])
                            _output = dlgen.generate_directory_listing(_path)
                            _node = init_node(_parent, _components[-1], _output)
                            nodes[missing].append((_components, _node))
                            new_outputs.append(_output)
                            _parent = _node
                        parent = _parent
                        break
                if parent:
                    break

        try:
            assert parent
        except AssertionError as e:
            e.args += (depth, precursor.components, nodes[depth-1])
            raise
        node = init_node(parent, precursor.name, output)
        nodes[depth].append((precursor.components, node))

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
