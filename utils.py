import posixpath as osp

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
