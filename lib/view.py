import lib.delegate

import pigui.pyqt5.model
import pigui.pyqt5.widgets.delegate
import pigui.pyqt5.widgets.list.view

DefaultList = pigui.pyqt5.widgets.list.view.DefaultList


def create_delegate(self, index):
    typ = self.model.data(index, 'type')

    if typ == 'disk':
        label = self.model.data(index, 'display')
        if self.model.data(index, key='group'):
            return lib.delegate.FolderDelegate(label, index)
        else:
            return lib.delegate.FileDelegate(label, index)

    elif typ == 'version':
        label = self.model.data(index, 'display')
        return lib.delegate.VersionDelegate(label, index)

    elif typ == 'command':
        label = self.model.data(index, 'command')
        return pigui.pyqt5.widgets.delegate.CommandDelegate(label, index)

    else:
        return super(DefaultList, self).create_delegate(index)


def monkey_patch():
    """The alteration is minimal enough for
    a monkey-patch to suffice"""
    DefaultList.create_delegate = create_delegate
