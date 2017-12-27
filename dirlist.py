import posixpath as osp

from pelican.generators import Generator
from pelican.outputs import HTMLOutput

class DirListGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(DirListGenerator, self).__init__(*args, **kwargs)

        self.template = self.get_template(self.settings.get("DIRLIST_TEMPLATE",
                                                            "dirlist"))

    def generate_directory_listing(self, path):
        path = osp.join(path, 'index.html')
        output = HTMLOutput(path, self.template, self.settings['RELATIVE_URLS'])
        return output
