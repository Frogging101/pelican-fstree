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

def render_tree(node):
    out = ""
    if node.parent:
        out += indent(node)
    out += node.name
    out += '<br>\n'
    for child in node.children:
        out += render_tree(child)
    return out
