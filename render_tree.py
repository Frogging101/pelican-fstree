from copy import deepcopy
from fnmatch import fnmatch
import os.path as osp

from . import unicode_box_drawing as bd
from .fsnode import Node

SEP = 2
SPACE = 1
SPACER = u'\u00a0'

"""Description of output
.
├── level1
│   ├── file
│   └── level2
│       ├── file
│       ├── level3
│       │   └── file
│       └── zfile
└── myfile
^^^^
||||-- Space (1 char)
|||
|||----- Separator (2 chars)
|--------- Node (1 char)
"""
def indent(node, root=None, style='light'):
    indent = '<span class="fsnode-indent">'
    ancestors = node.ancestors
    if root:
        if node is root:
            return ''
        else:
            ancestors = ancestors[ancestors.index(root):]
    for i,a in enumerate(ancestors):
        class_ = "fsnode-node"
        if i == 0:
            continue
        if a.level.index(a) < len(a.level)-1:
            _node = bd.vert[style]
            class_ += " fsnode-vert"
        else:
            _node = SPACER

        sep = SPACER * SEP
        space = SPACER * SPACE

        indent += '<span class="{}">'.format(class_) + _node + "</span>" +\
                  sep + space

    class_ = "fsnode-node"
    if node.level.index(node) < len(node.level)-1:
        _node = bd.vertright[style]
        class_ += " fsnode-vert"
    else:
        _node = bd.upright[style]

    sep = bd.horz[style] * SEP
    space = SPACER * SPACE
    indent += '<span class="{}">'.format(class_) + _node + "</span>" +\
              sep + space
    indent += "</span>"
    return indent

"""Prunes the tree given lists of paths to keep and paths to prune.

The items in the given lists of paths are treated as shell-style globs
via fnmatch.

Paths matching an expression in matchpaths will be kept to the exclusion
of others. If matchpaths is empty or none, then all paths will be
matched.

Paths matching an expression in ignorepaths will be unconditionally
pruned.

Recursive function, returns True if the given node should be deleted.
"""
def prune_tree(node, matchpaths, ignorepaths):
    ret = True # Prune by default

    if not matchpaths and not ignorepaths:
        # Short circuit case where there are no paths to check against
        return False

    if matchpaths:
        for matchpath in matchpaths:
            if fnmatch(node.path, matchpath):
                ret = False # Keep matched paths
    else:
        # Match all paths if matchpaths is empty/None
        ret = False

    if ignorepaths:
        for ignorepath in ignorepaths:
            if fnmatch(node.path, ignorepath):
                ret = True # Prune ignored paths

    for child in node.children:
        if prune_tree(child, matchpaths, ignorepaths):
            node.del_child(child)
        else:
            # Don't prune the current node if it has an unpruned child
            ret = False
    return ret


def _render_tree(node, settings, descendants, me, root):
    out = '<div class="fsnode">'
    if node is not root:
        out += indent(node, root)

    extlink = ''
    if hasattr(node, 'link_dest'):
        extlink = 'class="extlink"'
    out += '<a href="{}" {}>{}</a>'.format(
        node.get_url(settings.get('SITEURL', '')), extlink, node.name)
    out += '</div>\n'
    if descendants:
        for child in node.children:
            out += _render_tree(child, settings, descendants-1, me, root)
    return out

def render_tree(node, settings, descendants=-1, me=None, matchpaths=None,
                ignorepaths=None):
    node = deepcopy(node)
    prune_tree(node, matchpaths, ignorepaths)
    if me is None:
        me = node
    else:
        me = node.get_node_at(me.path)
    return _render_tree(node, settings, descendants, me, node)

def render_tree_ancestors(node, settings, ancestors=-1, descendants=-1):
    me = node
    while ancestors and node.parent is not None:
        node = node.parent
        ancestors -= 1
        if descendants >= 0:
            # Increment descendants by one for each level we go up so
            # that it stays relative to the given node
            descendants += 1

    return render_tree(node, settings, descendants, me,
                       (me.path, osp.join(me.path, '*')))
