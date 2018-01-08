import posixpath as osp

from pelican.utils import posixize_path

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
