"""Business-logic of Lib"""

import os

# pifou library
import pifou.lib

# local library
import lib.model
import lib.settings
import lib.controller

# pifou dependency
import zmq


@pifou.lib.log
class Lib(object):
    """Lib Application

    Arguments:
        outport (int): Port at which to transmit messages
        support (tuple): File-extensions to display commands for

    Attributes:
        controller: Associated controller to this application
        model: Associated model to this application
        outsocket: Reference to socket used to transmit messages

    """

    def __init__(self, outport=None, support=tuple()):
        self.controller = None
        self.model = None
        self.outport = outport
        self.support = support
        self.outsocket = None

        if outport:
            self.log.info("Establishing connection to {}".format(outport))
            context = zmq.Context.instance()
            self.outsocket = context.socket(zmq.PUSH)
            self.outsocket.connect("tcp://127.0.0.1:{}".format(outport))
        else:
            self.log.warning("Offline..")

    def set_model(self, model):
        self.model = model

    def set_controller(self, controller):
        self.controller = controller
        controller.import_version.connect(self.import_version)
        controller.import_file.connect(self.import_file)

    def import_version(self, path):
        """Import domain-version at `path`

        Arguments:
            path (str): Absolute path to domain object

        """

        if not self.outsocket:
            info = "No receiver found"
            self.error(info)
            return self.controller.notify(info)

        info = "Importing domain version: {}".format(path)
        self.info(info)

        supported_ext = self.support
        supported_files = list()

        if not os.path.isdir(path):
            return self.error('{} is not a directory'.format(path))

        self.log.info("Looking for supported files in domain-version:"
                      "%r" % supported_ext)

        for _, _, files in os.walk(path):
            for f in files:
                name, ext = os.path.splitext(f)
                if ext.lower() in supported_ext:
                    supported_files.append(f)
            break

        if not len(supported_files) == 1:
            info = "No supported files found"
            self.log.error(info)
            return self.error(info)

        path = os.path.join(path, files[0])
        self.info("About to import {}".format(path))
        self.import_file(path)

    def import_file(self, path):
        """Import `path`

        Arguments:
            path (str): Absolute path to file

        """

        self.outsocket.send_json(
            {'type': 'command',
             'command': 'import',
             'payload': path})

    def info(self, message):
        self.log.info(message)
        self.outsocket.send_json(
            {'type': 'info',
             'payload': message})

    def error(self, message):
        self.log.error(message)
        self.outsocket.send_json(
            {'type': 'error',
             'payload': message})


if __name__ == '__main__':
    import pigui.pyqt5.util

    application = Lib()

    with pigui.pyqt5.util.application_context():
        controller = lib.controller.Lib()

        model = lib.model.Model()
        controller.set_model(model)
        application.set_model(model)

        application.set_controller(controller)

        controller.resize(*lib.settings.WINDOW_SIZE)
        controller.animated_show()

        model.setup(r'C:\studio\content\jobs\machine\content')
