import posixpath as osp
from functools import partial

from pelican import contents
from pelican.outputs import HTMLOutput

from .fsnode import Node, NodePrecursor as NP
from .render_tree import render_tree, render_tree_ancestors
from .utils import normalize_path, split_path

class FSTree:
    def __init__(self, settings, dlgen):
        self.settings = settings
        self.dlgen = dlgen
        self.precursors = []

    """Initialize a Node with a parent (optional), name, and Output object.

    The new Node is added to the parent's list of children, and a reference
    to it is stored in the Output object's "node" template variable.
    """
    def init_node(self, precursor, parent):
        node = precursor.instantiate(parent)
        node.render_tree = partial(render_tree, node, self.settings)
        node.render_tree_ancestors = partial(render_tree_ancestors, node, self.settings)
        node.output.template_vars['node'] = node
        return node

    """Generates the tree and links each Output object to a Node.

    Nodes will be stored in the corresponding Output object's "node"
    template variable by init_node().
    """
    def add_nodes(self, generators, outputs):
        # Convert outputs to precursors
        for output in outputs:
            if type(output) is HTMLOutput:
                self.precursors.append(NP(normalize_path(output.path), output))

        # Test for duplicate paths
        paths = [p.path for p in self.precursors]
        try:
            assert len(paths) == len(set(paths)), "we got dupes"
        except AssertionError as e:
            e.args += (paths,)
            raise

        # Sort precursors in ascending order of number of path components
        self.precursors.sort(key=lambda item: len(item.components))

        # Create root node for precursor with first (shortest) path
        root = self.init_node(self.precursors[0], None)
        # Indexed by depth, nodes[0] contains only ('/', root).
        nodes = [[(self.precursors[0].components, root)]]
        self.precursors.pop(0)

        # Create the rest of the nodes
        for precursor in self.precursors:
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
                                _output = self.dlgen.generate_dirindex(_path)
                                _precursor = NP(_path, _output)
                                _node = self.init_node(_precursor, _parent)
                                nodes[missing].append((_components, _node))
                                outputs.append(_output)
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

            if not precursor.output:
                precursor.output = self.dlgen.generate_dirindex(
                    precursor.path)
                outputs.append(precursor.output)

            node = self.init_node(precursor, parent)
            nodes[depth].append((precursor.components, node))

    """Store source directory (with trailing slash) in
    content.metadata['dir'].

    Some leading components (such as those in PAGE_PATHS for pages) are
    removed.
    """
    def add_dir(self, content):
        if content.source_path is None:
            return

        dirname = content.relative_dir
        if type(content) == contents.Page:
            dirname = dirname.replace(osp.commonprefix(
                    self.settings['PAGE_PATHS'] + [dirname,]),
                '')

        if dirname:
            # Remove leading slash
            if osp.isabs(dirname):
                dirname = osp.relpath(dirname, '/')
            # Add trailing slash
            dirname += '/'

        content.metadata['dir'] = dirname
