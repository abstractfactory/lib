from __future__ import absolute_import

# standard library
import os

# pifou library
import pifou.lib

# pifou dependencies
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# pigui library
import pigui
import pigui.style
import pigui.pyqt5.widgets.delegate
import pigui.pyqt5.widgets.application
import pigui.pyqt5.widgets.miller.view

# local library
import lib.view
import lib.model
import lib.settings

pigui.style.register('lib')
lib.view.monkey_patch()


@pifou.lib.log
class Lib(pigui.pyqt5.widgets.application.widget.ApplicationBase):
    """
    Signals:
        import_version (str): A domain-version is being imported
        import_file (str): A plain file is being imported

    """

    import_version = QtCore.pyqtSignal(str)
    import_file = QtCore.pyqtSignal(str)

    def __init__(self, support=tuple(), parent=None):
        """
        Arguments:
            parent (QtWidgets.QWidget): Qt parent of this widget

        """

        super(Lib, self).__init__(parent)
        self.setWindowTitle('Lib')

        # Pad the view, and inset background via CSS
        canvas = QtWidgets.QWidget()
        canvas.setObjectName('Canvas')

        view = pigui.pyqt5.widgets.miller.view.DefaultMiller()
        view.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)

        layout = QtWidgets.QHBoxLayout(canvas)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(view)

        widget = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(canvas)
        layout.setContentsMargins(5, 0, 5, 5)
        layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        self.set_widget(widget)

        self.view = view
        self.model = None
        self.support = support

    def set_model(self, model):
        """Set model for this controller

        Arguments:
            model (pifou.pyqt5.model.Model): Target model

        """

        self.view.set_model(model)
        self.model = model

    def event(self, event):
        """Event handlers

        Handled events:
            OpenInExplorerEvent -- An item is being explored
            OpenInAboutEvent -- An item is being explored, in About

        """

        def open_explorer(index):
            """Open `index` in file-system explorer

            Arguments:
                index (str): Index to open

            """

            path = self.model.data(event.index, 'path')
            pigui.service.open_in_explorer(path)

        def open_about(index):
            """Open `index` in About

            Arguments:
                index (str): Index to open

            """

            path = self.model.data(event.index, 'path')
            pigui.service.open_in_about(path)

        def command(index):
            """A command delegate was pressed

            Arguments:
                index (str): Index of file to open

            Sources:
                Imports may happen on either Versions or Files

            """

            command = self.model.data(index, key='command')
            if command == 'import':
                source = self.model.data(index, key='source')
                parent = self.model.data(index, key='parent')
                path = self.model.data(parent, key='path')

                if source == 'version':
                    self.import_version.emit(path)

                if source == 'file':
                    self.import_file.emit(path)

                basename = os.path.basename(path)
                self.notify("Importing %s" % basename)

        # Handled events
        OpenInExplorerEvent = pigui.pyqt5.event.Type.OpenInExplorerEvent
        OpenInAboutEvent = pigui.pyqt5.event.Type.OpenInAboutEvent
        CommandEvent = pigui.pyqt5.event.Type.CommandEvent

        handler = {OpenInExplorerEvent: open_explorer,
                   OpenInAboutEvent: open_about,
                   CommandEvent: command}.get(event.type())

        if handler:
            handler(event.index)

        return super(Lib, self).event(event)


if __name__ == '__main__':
    import pifou
    import pigui
    pifou.setup_log()
    pigui.setup_log()

    import pigui.pyqt5.util

    with pigui.pyqt5.util.application_context():

        model = lib.model.Model()

        win = Lib()
        win.set_model(model)
        win.resize(*lib.settings.WINDOW_SIZE)
        win.animated_show()

        model.setup(r'C:\studio\content\jobs\machine\content')
