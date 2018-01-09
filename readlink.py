import posixpath as osp

from pelican.contents import Content
from pelican.generators import Generator
from pelican.readers import BaseReader
from pelican.utils import pelican_open

from .fsnode import LinkNodePrecursor
from .utils import normalize_path

class LinkReader(BaseReader):
    enabled = True
    file_extensions = ['lnk']

    def read(self, filename):
        source_path = osp.relpath(filename, self.settings['PATH'])
        path = normalize_path(osp.splitext(source_path)[0])
        with pelican_open(filename) as content:
            if content[-1] == '\n':
                content = content[:-1]
            link = content

        # XX Hack: 'precursors' is injected into this module in __init__.py
        precursors.append(LinkNodePrecursor(path, link))
        return None, {}

class LinkContent(Content):
    mandatory_properties = ()
    default_template = ''

class LinkGenerator(Generator):
    def generate_context(self):
        for f in self.get_files(self.settings.get("LINK_PATHS", ['']),
                                extensions=['lnk']):
            self.readers.read_file(self.path, f, LinkContent)
