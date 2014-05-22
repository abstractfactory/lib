from __future__ import absolute_import

# pifou library
import pifou.lib
import pifou.signal

# pifou dependencies
from PyQt5 import QtWidgets

# pigui library
import pigui
import pigui.util
import pigui.style
import pigui.widgets.pyqt5.item
import pigui.widgets.pyqt5.application
import pigui.widgets.pyqt5.miller.view

# local library
import lib
import lib.item
import lib.view

lib.item.register()
lib.view.register()

pigui.style.register('lib')


@pifou.lib.log
class Lib(pigui.widgets.pyqt5.application.Base):

    WINDOW_SIZE = (700, 400)  # w/h
    WINDOW_POSITION = None

    def __init__(self, *args, **kwargs):
        super(Lib, self).__init__(*args, **kwargs)

        # Signals
        self.imported = pifou.signal.Signal(path=str)

        def setup_body():
            body = QtWidgets.QWidget()

            view = pigui.widgets.pyqt5.miller.view.DefaultMiller()
            view.setObjectName('MillerView')
            view.event.connect(self.event_handler)

            layout = QtWidgets.QHBoxLayout(body)
            layout.addWidget(view)
            layout.setContentsMargins(0, 0, 0, 0)

            return body

        body = setup_body()

        superclass = super(Lib, self)
        container = superclass.findChild(QtWidgets.QWidget, 'Container')
        layout = container.layout()
        layout.addWidget(body)
        layout.setContentsMargins(5, 0, 5, 5)

        self.resize(*self.WINDOW_SIZE)

    def init_application(self, application):
        application.loaded.connect(self.load)
        application.killed.connect(self.killed_event)
        self.application = application

    def killed_event(self):
        self.close()

    def load(self, node):
        item = pigui.widgets.pyqt5.item.TreeItem.from_node(node)
        view = self.findChild(QtWidgets.QWidget, 'MillerView')
        view.load(item)

    def event_handler(self, name, data):
        """
        Process events coming up from within the
        hierarchy of widgets.
                          _______________
                         |               |
                         |     Event     |
                         |_______________|
                                 |
                          _______v_______
                         |               |
                         |    Handler    |
                         |_______________|
                                 |
                 ________________|_______________
                |                |               |
         _______v______   _______v______   ______v_______
        |              | |              | |              |
        |   Response   | |   Response   | |   Response   |
        |______________| |______________| |______________|

        """

        #  _____________
        # |             |
        # |   Command   |
        # |_____________|
        #
        if name == 'command':
            item = data[0]
            subject = item.data.get('subject')
            command = item.data.get('command')

            #  ____________
            # |            |
            # |   Import   |
            # |____________|
            #
            if command == 'import':
                self.imported.emit(path=subject.node.path.as_str)
