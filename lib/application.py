
# standard library
import threading

# pifou library
import pifou.lib
import pifou.signal
import pifou.process
import pifou.pom.node

import pifou.com.util
import pifou.com.pyzmq.rpc

import pifou.com.pyzmq.endpoint
import pifou.com.constant

# pifou dependencies
import zmq

context = zmq.Context()

local_ip = pifou.com.util.local_ip()

# Shorthands
protocol = "tcp://{ip}:{port}"
constant = pifou.com.constant
endpoint = pifou.com.pyzmq.endpoint


@pifou.lib.Process.cascading
def hide_extensions(node):
    if not node.isparent:
        if not node.path.suffix.lower() in ('ma', 'mb', 'obj'):
            return

    return node


@pifou.lib.log
class Invoker(object):
    """Resolve requests and maintain history/future"""

    def __init__(self, ip='127.0.0.1'):
        """
        Channels:
            Commands (async) - Send commands and receive results
            Init (sync) - Configure server

        Args:
            ip (str): IP to connect
            port (str): Port to connect

        """

        self.information = pifou.signal.Signal(header=str, body=str)

        # Prepare out-messages
        #  __________
        # |          |
        # |   --->   |
        # |__________|

        init_out = "tcp://localhost:7000"
        commands_in = "tcp://*:7002"
        commands_out = "tcp://localhost:7001"

        self.init_out = endpoint.create_producer(init_out)
        self.commands_in = endpoint.create_consumer(commands_in)
        self.commands_out = endpoint.create_producer(commands_out)

        # Prepare in-messages
        #  __________
        # |          |
        # |   <---   |
        # |__________|

        self.register("tcp://%s:6000" % local_ip)
        self.listen_commands()

    def listen_commands(self):
        def process_command(message):
            info = message.get(constant.INFO)
            error = message.get(constant.ERROR)

            if info:
                self.log.info(info)
                self.information.emit(header='Results',
                                      body=info)

            if error:
                self.log.error(error)
                self.information.emit(header='Error',
                                      body=error)

            message = {constant.STATUS: constant.OK}
            return message

        def thread():
            while True:
                #  __________
                # |          |
                # |   <---   |
                # |__________|
                in_message = self.commands_in.recv_json()

                #  __________
                # |          |
                # |   /\/\   |
                # |__________|
                out_message = process_command(in_message)

                # Prepare output
                #  __________
                # |          |
                # |   --->   |
                # |__________|
                self.commands_in.send_json(out_message)

        thread = threading.Thread(target=thread,
                                  name='listen_commands')
        thread.daemon = True
        thread.start()

        self.log.info("Listening on commands..")

    def register(self, endpoint):
        message = {'command': 'connect', 'id': endpoint}
        self.init_out.send_json(message)
        self.init_out.recv_json()
        self.commands_id = endpoint

    def import_(self, path):
        return self.execute('import', path)

    def execute(self, command, *args, **kwargs):
        """Perform command"""

        message = {
            constant.COMMAND: command,
            constant.ARGS: args,
            constant.KWARGS: kwargs,
            constant.ID: self.commands_id
        }

        self.commands_out.send_json(message)
        confirmation = self.commands_out.recv_json()

        if confirmation[constant.STATUS] != constant.OK:
            error_message = confirmation[constant.INFO]
            self.log.error(error_message)

        return message


@pifou.lib.log
class Lib(object):
    """Business logic of Lib

    Command Pattern:
        In the context of the Command Pattern, this
        class represents the `Client`.

    Reference:
        http://www.oodesign.com/command-pattern.html

    """

    def __init__(self,
                 extensions=[],
                 representation=None):

        self.extensions = extensions
        self.representation = representation

        # Signal
        self.loaded = pifou.signal.Signal(node=object)
        self.killed = pifou.signal.Signal()
        self.information = pifou.signal.Signal(header=str, body=str)

        self.node = None

        invoker = Invoker()
        invoker.information.connect(self.information)

        self.invoker = invoker

    def init_widget(self, widget):
        widget.init_application(self)
        widget.imported.connect(self.import_event)
        widget.animated_show()

        self.widget = widget

    def load(self, url):
        node = pifou.pom.node.Node.from_str(url)
        node.children.preprocess.add(pifou.process.pre_junction)
        node.children.postprocess.add(pifou.process.post_hide_hidden)

        # Isolate extensions
        node.children.postprocess.add(hide_extensions)

        self.loaded.emit(node=node)

        self.node = node

    def import_event(self, path):
        self.invoker.import_(path)


if __name__ == '__main__':
    pass