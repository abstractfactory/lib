
# pifou library
import pifou.lib
import pifou.signal
import pifou.pom.node
import pifou.com.source

# pigui library
import pigui.widgets.pyqt5.list.view
import pigui.widgets.pyqt5.miller.view

# local library
import lib.item


class List(pigui.widgets.pyqt5.list.view.DefaultList):

    predicate = pigui.widgets.pyqt5.miller.view.DefaultMiller

    def __init__(self, *args, **kwargs):
        super(List, self).__init__(*args, **kwargs)

    def item_added_event(self, item):
        super(List, self).item_added_event(item)

    def load(self, item):
        super(List, self).load(item)

        if item.node.isparent:
            self.append_merged_items(item)
        else:
            self.append_file_commands(item)

    def append_merged_items(self, item):
        """
         _______
        |       |
        | Merge |
        |_______|

        """

        # Add anything under $CD/public
        path = item.node.path
        path = path + 'public'

        # .copy rather than instantiate a new, so as
        # to maintain any processes present within
        # the original.
        public = item.node.copy(path=path.as_str)

        pifou.com.source.disk.pull(public)
        for version in public:
            version_item = item.from_node(version)
            self.add_item(version_item)

        # Add anything under $CD/public/$REPRESENTATION

    def append_file_commands(self, item):
        """
         _________________
        |                 |
        |  File Commands  |
        |_________________|

        """

        for command in ('import', 'reference'):
            command_item = lib.item.Item.from_type('%s.command' % command)
            command_item.data['command'] = command
            command_item.data['subject'] = item
            pol = command_item.sortpolicy
            pol.position = pol.AlwaysAtBottom
            self.add_item(command_item)

            if command == 'reference':
                command_item.widget.setEnabled(False)


def register():
    pigui.widgets.pyqt5.miller.view.DefaultMiller.register(List)
