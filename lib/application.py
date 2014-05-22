
# pifou library
import pifou.lib
import pifou.signal
import pifou.process
import pifou.pom.node

import pifou.com.util
import pifou.com.pyzmq.rpc

# pifou dependencies
import zmq

import lib.command

# Each running client will have a unique ID
# The server uses this ID to separate between commands
# being executed and allows multiple clients to undo/redo
# their own individual commands.
# UUID = str(uuid.uuid4())
# client_endpoint = "tcp://*:6001"#.format(ip=pifou.com.util.local_ip())

context = zmq.Context()
local_ip = pifou.com.util.local_ip()


@pifou.lib.Process.cascading
def hide_extensions(node):
    if not node.isparent:
        if not node.path.suffix.lower() in ('ma', 'mb', 'obj'):
            return

    return node


@pifou.lib.log
class Invoker(object):
    """Resolve requests and maintain history/future"""

    MAX_RETRIES = 3
    CLIENT_ENDPOINT = "tcp://{ip}:6002"

    def __init__(self, ip='localhost', port='6000'):
        self.outgoing = context.socket(zmq.REQ)
        self.incoming = context.socket(zmq.REP)

        self.outgoing_ip = ip
        self.outgoing_port = port

        self.connect()

    def connect(self):
        """Register invoker with receiver"""

        # Outgoing
        #  __________
        # |          |
        # |   --->   |
        # |__________|

        endpoint = "tcp://{ip}:{port}".format(
            ip=self.outgoing_ip,
            port=self.outgoing_port)

        self.log.info("Connecting to %s.." % endpoint)
        self.outgoing.connect(endpoint)
        self.log.info("Connected.")

        # Incoming
        #  __________
        # |          |
        # |   <---   |
        # |__________|

        bind_endpoint = self.CLIENT_ENDPOINT.format(ip='*')
        self.log.info("Binding to %s.." % bind_endpoint)
        self.incoming.bind(bind_endpoint)
        self.log.info("Bound")

        connect_endpoint = self.CLIENT_ENDPOINT.format(ip=local_ip)
        command = lib.command.ConnectCommand(endpoint=connect_endpoint)
        message = command.to_message()

        self.log.info("Registering %r with server" % connect_endpoint)
        self.outgoing.send_json(message)
        message = self.outgoing.recv_json()
        response = lib.command.Response.from_message(message)
        self.log.info("Registered.")

        if not response.status == response.OK:
            print response.status

    def import_(self, path):
        command = lib.command.ImportCommand(path)
        return self.execute(command)

    def execute(self, command):
        """Perform command"""
        command.id = self.CLIENT_ENDPOINT.format(ip=local_ip)

        message = command.to_message()

        self.log.info("Sending command..")
        self.outgoing.send_json(message)
        self.log.info("Complete.. awaiting response..")
        message = self.outgoing.recv_json()

        response = lib.command.Response.from_message(message)

        self.log.info("Response received")

        if not response.status == 'ok':
            print "Request failed"

    def listen(self):
        pass
        # def result_from_commands():
        #     while True:
        #         message = self.results.recv_json()
        #         reply = lib.command.Result.from_message(message)


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

        self.node = None

        self.invoker = Invoker()

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
        print "Importing %s" % path
        self.invoker.import_(path)
