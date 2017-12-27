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
    indent = ""
    ancestors = node.ancestors
    if root:
        if node is root:
            return ''
        else:
            ancestors = ancestors[ancestors.index(root):]
    for i,a in enumerate(ancestors):
        if i == 0:
            continue
        if a.level.index(a) < len(a.level)-1:
            _node = bd.vert[style]
        else:
            _node = SPACER

        sep = SPACER * SEP
        space = SPACER * SPACE

        indent += _node + sep + space

    if node.level.index(node) < len(node.level)-1:
        _node = bd.vertright[style]
    else:
        _node = bd.upright[style]

    sep = bd.horz[style] * SEP
    space = SPACER * SPACE
    indent += _node + sep + space
    return indent

def prune_tree(node, matchpaths, ignorepaths):
    ret = 1
    for matchpath in matchpaths:
        if fnmatch(node.path, matchpath):
            ret = 0
    for ignorepath in ignorepaths:
        if fnmatch(node.path, ignorepath):
            ret = 1
    for child in node.children:
        if prune_tree(child, matchpaths, ignorepaths):
            node.del_child(child)
        else:
            ret = 0
    return ret


def _render_tree(node, settings, descendants, me, root):
    out = ""
    if node is not root:
        out += indent(node, root)
    out += '<a href="{}{}">{}</a>'.format(settings.get('SITEURL', ''),
                                          node.path, node.name)
    out += '<br>\n'
    if descendants:
        for child in node.children:
            out += _render_tree(child, settings, descendants-1, me, root)
    return out

def render_tree(node, settings, descendants=-1, me=None, matchpaths=("*",),
                ignorepaths=("",)):
    node = deepcopy(node)
    prune_tree(node, matchpaths, ignorepaths)
    if me is None:
        me = node
    else:
        me = node.get_node_at(me.path)
    return _render_tree(node, settings, descendants, me, node)

def render_tree_ancestors(node, settings, ancestors, descendants=-1):
    me = node
    while ancestors and node.parent is not None:
        node = node.parent
        ancestors -= 1

    return render_tree(node, settings, descendants, me,
                       (me.path, osp.join(me.path, '*')))
