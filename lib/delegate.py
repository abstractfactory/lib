
"""Dashboard-specific delegates"""

# pifou library
import pifou
import pifou.om
import pifou.signal
import pifou.pom.domain

# pifou dependencies
from PyQt5 import QtWidgets

# pigui library
import pigui.service
import pigui.pyqt5.event
import pigui.pyqt5.widgets.delegate


class FolderDelegate(pigui.pyqt5.widgets.delegate.FolderDelegate):
    """Append context-menu"""

    def action_event(self, state):
        action = self.sender()
        label = action.text()

        if label == "Open in About":
            event = pigui.pyqt5.event.OpenInAboutEvent(index=self.index)
            QtWidgets.QApplication.postEvent(self, event)

        elif label == "Open in Explorer":
            event = pigui.pyqt5.event.OpenInExplorerEvent(index=self.index)
            QtWidgets.QApplication.postEvent(self, event)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        for label in ("Open in About",
                      "Open in Explorer"):
            action = QtWidgets.QAction(label,
                                       self,
                                       triggered=self.action_event)
            menu.addAction(action)

        menu.exec_(event.globalPos())


class FileDelegate(pigui.pyqt5.widgets.delegate.FileDelegate):
    pass


class VersionDelegate(FolderDelegate):
    pass


if __name__ == '__main__':
    import pifou.pom.node
    import pigui.pyqt5.util

    # register()

    with pigui.pyqt5.util.application_context():
        path = r'S:\content\jobs\skydivers'
        node = pifou.pom.node.Node.from_str(path)
        delegate = FolderDelegate(node.path.as_str, index='hello')

        delegate.show()
