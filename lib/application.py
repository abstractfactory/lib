import os

# local library
import lib.model
import lib.settings
import lib.controller

# pifou dependency
import zmq


class Lib(object):
    def __init__(self, port=None, support=tuple()):
        self.controller = None
        self.model = None
        self.port = port
        self.support = support

    def set_model(self, model):
        self.model = model

    def set_controller(self, controller):
        self.controller = controller
        controller.import_version.connect(self.import_version)
        controller.import_file.connect(self.import_file)

    def import_version(self, path):
        """Import domain-version `path`

        Arguments:
            path (str): Absolute path to domain object

        """

        if not self.port:
            raise ValueError("No receiver found")

        supported_ext = self.support
        files = list()

        assert os.path.isdir(path)
        for f in os.listdir(path):
            name, ext = os.path.splitext(f)
            if ext.lower() in supported_ext:
                files.append(f)

        assert len(files) == 1

        path = os.path.join(path, files[0])
        self.import_file(path)

    def import_file(self, path):
        """Import `path`

        Arguments:
            path (str): Absolute path to file

        """

        msg = {'type': 'command',
               'command': 'import_version',
               'path': path}

        context = zmq.Context.instance()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:{}".format(self.port))
        socket.send_json(msg)

        recv = socket.recv_json()
        if not recv.get('status') == 'ok':
            raise ValueError("Host did not accept: %s -> %s" % (msg, recv))


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
