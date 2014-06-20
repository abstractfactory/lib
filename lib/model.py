
# pigui library
import pifou.pom.node
import pifou.pom.domain
import pifou.com.source

# pigui library
import pigui.pyqt5.model

Version = 'version'


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

        if not value and self.data('type') in (pigui.pyqt5.model.Disk,
                                               Version):
            if key == 'path':
                node = self.data('node')
                return node.path.as_str

            if key == 'display':
                node = self.data('node')
                return node.path.name

            if key == 'group':
                node = self.data('node')
                return node.isparent

        return value


class Model(pigui.pyqt5.model.Model):
    def setup(self, path):
        node = pifou.pom.node.Node.from_str(path)
        root = self.create_item({'type': 'disk',
                                 'node': node})
        self.root_item = root
        self.model_reset.emit()

    def create_item(self, data, parent=None):
        assert isinstance(parent, basestring) or parent is None
        item = Item(data, parent=self.indexes.get(parent))
        self.register_item(item)
        return item

    def pull(self, index):
        if self.data(index, 'type') == 'disk':
            node = self.data(index, 'node')

            try:
                pifou.com.source.disk.pull(node)
            except pifou.error.Exists:
                self.status.emit("%s did not exist" % node.path)

            for child in node.children:
                if child.path.name.startswith('.'):
                    continue

                self.create_item({'type': 'disk',
                                  'node': child}, parent=index)

            # Append versions
            asset = pifou.pom.domain.Entity.from_node(node)
            for version in asset.versions:
                self.create_item({'type': 'version',
                                  'node': version,
                                  'sortkey': '|'}, parent=index)

        # Append commands to versions
        if self.data(index, 'type') == 'version':
            node = self.data(index, 'node')

            for command in ('import',):
                self.create_item({'type': 'command',
                                  'node': node,
                                  'command': command,
                                  'sortkey': '{',
                                  'parent': index}, parent=index)

        super(Model, self).pull(index)
