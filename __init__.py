from pelican import signals

from .dirlist import DirListGenerator
from . import fstree
from .fstree import FSTree
from . import readlink
from .readlink import LinkReader, LinkGenerator

class FSTreePlugin:
    def __init__(self):
        self.fstree = None
        self.settings = None
        self.dlgen = None
        self.precursors = []
        readlink.precursors = self.precursors

    def try_init_fstree(self):
        if self.fstree is None:
            if self.settings is not None and self.dlgen is not None:
                self.fstree = FSTree(self.settings, self.dlgen, self.precursors)

    def init(self, pelican):
        self.settings = pelican.settings

    def add_dirlist_generator(self, pelican):
        return DirListGenerator

    def add_link_generator(self, pelican):
        return LinkGenerator

    def get_dirlist_generator(self, generator):
        if isinstance(generator, DirListGenerator):
            self.dlgen = generator

    def gen_archive_links(self, article_generator):
        fstree.gen_archive_links(article_generator.dates, self.settings,
                                 self.precursors)

    def add_nodes(self, generators, outputs):
        self.try_init_fstree()
        assert self.fstree
        self.fstree.add_nodes(generators, outputs)

    def add_dir(self, content):
        self.try_init_fstree()
        assert self.fstree
        self.fstree.add_dir(content)

    def add_link_reader(self, readers):
        readers.reader_classes['lnk'] = LinkReader

    def register(self):
        signals.initialized.connect(self.init)
        signals.readers_init.connect(self.add_link_reader)
        signals.get_generators.connect(self.add_dirlist_generator)
        signals.get_generators.connect(self.add_link_generator)
        signals.generator_init.connect(self.get_dirlist_generator)
        signals.article_generator_finalized.connect(self.gen_archive_links)
        signals.all_generators_finalized.connect(self.add_nodes)
        signals.content_object_init.connect(self.add_dir)

def register():
    global _plugin # If this goes out of scope, it will not receive signals
    _plugin = FSTreePlugin()
    _plugin.register()
