
# pifou library
import pifou.om
import pifou.signal

# pigui library
import pigui.service

import pigui.widgets.pyqt5.item

# pigui dependencies
from PyQt5 import QtWidgets

# local library
# import lib
# from lib import process


class Item(pigui.widgets.pyqt5.item.TreeItem):
    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        self.widget.open_in_about.connect(self.open_in_about)
        self.widget.open_in_explorer.connect(self.open_in_explorer)
        self.widget.hide.connect(self.hide_event)
        self.widget.setText(self.name)

    def open_in_about(self):
        path = self.node.url.path.as_str
        pigui.service.open_in_about(path)

    def open_in_explorer(self):
        self.data['debug'] = 'explore'
        self.event.emit(name='debug', data=[self])

        path = self.node.url.path.as_str
        pigui.service.open_in_explorer(str(path))

    def hide_event(self):
        path = self.node.url.path.as_str
        pifou.om.write(path, 'hidden', None)


class ItemWidget(pigui.widgets.pyqt5.item.TreeWidget):
    def __init__(self, *args, **kwargs):
        super(ItemWidget, self).__init__(*args, **kwargs)

        self.open_in_about_action = None
        self.open_in_explorer_action = None
        self.hide_action = None

        # Signals
        self.open_in_about = pifou.signal.Signal()
        self.open_in_explorer = pifou.signal.Signal()
        self.hide = pifou.signal.Signal()

        self.init_actions()

    def init_actions(self):
        # QActions transmit their checked-state, but we won't
        # make use of it in Item. We use lambda to silence that.
        oia_signal = lambda state: self.open_in_about.emit()
        oie_signal = lambda state: self.open_in_explorer.emit()
        hide_signal = lambda state: self.hide.emit()

        oia_action = QtWidgets.QAction("&Open in About", self,
                                       statusTip="Open in About",
                                       triggered=oia_signal)
        oie_action = QtWidgets.QAction("&Open in Explorer", self,
                                       statusTip="Open in Explorer",
                                       triggered=oie_signal)
        hide_action = QtWidgets.QAction("&Hide", self,
                                        statusTip="Hide folder",
                                        triggered=hide_signal)

        self.open_in_explorer_action = oie_action
        self.open_in_about_action = oia_action
        self.hide_action = hide_action

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        for action in (self.open_in_about_action,
                       self.open_in_explorer_action,
                       self.hide_action):

            if not action:
                continue

            menu.addAction(action)
        menu.exec_(event.globalPos())


class ItemFamily(object):
    predicate = None
    ItemClass = Item
    WidgetClass = ItemWidget


# class VersionFamily(object):
#     predicate = 'version'
#     ItemClass = VersionItem
#     WidgetClass = VersionWidget


def register():
    # pigui.widgets.pyqt5.item.Item.register(VersionFamily)
    pigui.widgets.pyqt5.item.Item.register(ItemFamily)
