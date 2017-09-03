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
def indent(node, style='light'):
    indent = ""
    ancestors = node.ancestors
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

def render_tree(node, settings, descendants=-1, me=None):
    if me is None:
        me = node
    out = ""
    if node.parent:
        out += indent(node)
    out += '<a href="{}{}">{}</a>'.format(settings.get('SITEURL', ''),
                                          node.path, node.name)
    out += '<br>\n'
    if descendants:
        for child in node.children:
            out += render_tree(child, settings, descendants-1, me)
    return out

def render_tree_ancestors(node, settings, ancestors, descendants=-1):
    me = node
    while ancestors and node.parent is not None:
        node = node.parent
        ancestors -= 1

    return render_tree(node, settings, descendants, me)
