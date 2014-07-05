
# standard library
import os

# pigui library
import pifou.com
import pifou.domain.version

# pigui library
import pigui.pyqt5.model

# Keys
VERSION = 'version'
DISPLAY = 'display'
TYPE = 'type'
PATH = 'path'
COMMAND = 'command'
SORTKEY = 'sortkey'
PARENT = 'parent'
SOURCE = 'source'

# Values
GROUP = 'group'
FILE = 'file'
DISK = 'disk'


class Iterator(pifou.com.Iterator):
    def __init__(self, *args, **kwargs):
        super(Iterator, self).__init__(*args, **kwargs)

        if not self.filter:
            self.filter = pifou.com.default_filter


class Item(pigui.pyqt5.model.ModelItem):
    """Dash-specific item

     _______________________
    |          Item         |
    |   ____________________|
    |  |__________________
    | |-                  |
    | |-       path       |
    | |-__________________|
    |__|

    """

    def data(self, key):
        """Intercept queries custom to Dash"""

        value = super(Item, self).data(key)

        if not value and self.data(TYPE) in (pigui.pyqt5.model.Disk,
                                             VERSION):
            if key == DISPLAY:
                path = self.data(PATH)
                display = os.path.basename(path)
                self.set_data(DISPLAY, display)
                return display

            if key == GROUP:
                path = self.data(PATH)
                isgroup = os.path.isdir(path)
                self.set_data(GROUP, isgroup)
                return isgroup

        return value


class Model(pigui.pyqt5.model.Model):
    def setup(self, path):
        root = self.create_item({TYPE: DISK,
                                 PATH: path})
        self.root_item = root
        self.model_reset.emit()

    def create_item(self, data, parent=None):
        assert isinstance(parent, basestring) or parent is None
        item = Item(data, parent=self.indexes.get(parent))
        self.register_item(item)
        return item

    def pull(self, index):
        """Pull data off of disk as per `index`

        Arguments:
            index (str): Index from which to pull

        Types:
            disk: Data is being are plain files/folders
            version: Data is the domain-object; VERSION
            command: Buttons that operate on `version` and `disk` types

        Item-data:
            type (str): Type of item
            sortkey (str): Override default sort-key
            command (str): When `type` is `command`, this contains its name
            parent (str): Reference to parent index (convenience data)
            source (str): Import can take place on two separate types of items.

        """

        if self.data(index, TYPE) == DISK:
            path = self.data(index, PATH)

            if self.data(index, GROUP):
                if os.path.exists(path):
                    for basename in Iterator(path):
                        if basename.startswith('.'):
                            continue

                        full_path = os.path.join(path, basename)
                        self.create_item({TYPE: DISK,
                                          PATH: full_path}, parent=index)
                else:
                    self.status.emit("%s did not exist" % path)

                # Append versions
                for version in pifou.domain.version.ls(path):
                    full_path = os.path.join(path, version)
                    self.create_item({TYPE: VERSION,
                                      PATH: full_path,
                                      SORTKEY: '|'}, parent=index)

        # Append commands to files and versions
        isversion = self.data(index, TYPE) == VERSION
        isfile = self.data(index, GROUP) is False

        if isversion or isfile:
            path = self.data(index, PATH)

            for command in ('import',):
                self.create_item({TYPE: COMMAND,
                                  PATH: path,
                                  COMMAND: command,
                                  SORTKEY: '{',
                                  PARENT: index,
                                  SOURCE: FILE if isfile else VERSION},
                                 parent=index)

        super(Model, self).pull(index)
