
# pigui library
import pifou.pom.node
import pifou.pom.domain
import pifou.com.source

# pigui library
import pigui.pyqt5.model

# Keys
VERSION = 'version'
DISPLAY = 'display'
TYPE = 'type'
NODE = 'node'
PATH = 'path'
COMMAND = 'command'
SORTKEY = 'sortkey'
PARENT = 'parent'
SOURCE = 'source'

# Values
GROUP = 'group'
FILE = 'file'
DISK = 'disk'


class Item(pigui.pyqt5.model.ModelItem):
    """Wrap pifou.pom.node in ModelItem

     _______________________
    |          Item         |
    |   ____________________|
    |  |__________________
    | |-                  |
    | |-  pifou.pom.node  |
    | |-__________________|
    |__|

    """

    def data(self, key):
        """Intercept queries custom to Dash

        Interceptions:
            disk: Disk queries are wrapped in pifou.pom.node
            version: Workspaces wrap nodes similar to disk

        """

        value = super(Item, self).data(key)

        if not value and self.data(TYPE) in (pigui.pyqt5.model.Disk,
                                             VERSION):
            if key == PATH:
                node = self.data(NODE)
                return node.path.as_str

            if key == DISPLAY:
                node = self.data(NODE)
                if self.data(GROUP):
                    return node.path.name
                else:
                    return node.path.basename

            if key == GROUP:
                node = self.data(NODE)
                return node.isparent

        return value


class Model(pigui.pyqt5.model.Model):
    def setup(self, path):
        node = pifou.pom.node.Node.from_str(path)
        root = self.create_item({TYPE: DISK,
                                 NODE: node})
        self.root_item = root
        self.model_reset.emit()

    def create_item(self, data, parent=None):
        assert isinstance(parent, basestring) or parent is None
        item = Item(data, parent=self.indexes.get(parent))
        self.register_item(item)
        return item

    def pull(self, index):
        """Pull data off of disk, based on `index`

        Arguments:
            index (str): Index from which to pull

        Types:
            disk: Data is being are plain files/folders
            version: Data is the domain-object; VERSION
            command: Buttons that operate on `version` and `disk` types

        Item-data
            type (str): Type of item
            node (pifou.pom.node): Domain object used for disk-access
            sortkey (str): Override default sort-key
            command (str): When `type` is `command`, this contains its name
            parent (str): Reference to parent index (convenience data)
            source (str): Import can take place on two separate types of items.

        """

        if self.data(index, TYPE) == DISK:
            node = self.data(index, NODE)

            if self.data(index, GROUP):
                try:
                    pifou.com.source.disk.pull(node)
                except pifou.error.Exists:
                    self.status.emit("%s did not exist" % node.path)

                for child in node.children:
                    if child.path.name.startswith('.'):
                        continue

                    self.create_item({TYPE: DISK,
                                      NODE: child}, parent=index)

                # Append versions
                asset = pifou.pom.domain.Entity.from_node(node)
                for version in asset.versions:
                    self.create_item({TYPE: VERSION,
                                      NODE: version,
                                      SORTKEY: '|'}, parent=index)

        # Append commands to files and versions
        isversion = self.data(index, TYPE) == VERSION
        isfile = self.data(index, GROUP) is False

        if isversion or isfile:
            node = self.data(index, NODE)

            for command in ('import',):
                self.create_item({TYPE: COMMAND,
                                  NODE: node,
                                  COMMAND: command,
                                  SORTKEY: '{',
                                  PARENT: index,
                                  SOURCE: FILE if isfile else VERSION},
                                 parent=index)

        super(Model, self).pull(index)
