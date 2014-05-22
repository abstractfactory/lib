# standard library
import threading
import Queue as queue

# pifou library
import pifou.lib

# pifou dependencies
import zmq


class Incomplete(Exception):
    pass


class AbstractMessage(object):
    def to_message(self):
        pass

    def from_message(self, message):
        pass


class AbstractRequest(AbstractMessage):
    COMMAND = 'command'
    ID = 'id'
    IP = 'ip'
    PORT = 'port'

    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def from_message(cls, message):
        pass

    def to_message(self):
        pass


class AbstractResponse(AbstractMessage):
    OK = 'ok'
    FAIL = 'fail'

    def __init__(self, status):
        self.status = status

    @classmethod
    def from_message(cls, message):
        return cls(status=message.get('status'))

    def to_message(self):
        return {
            'status': self.status
        }


class Request(AbstractRequest):
    """Sent asynchronously, from client to server
     __________          __________
    |          |        |          |
    |  Server  | -----> |  Client  |
    |__________|        |__________|

    """


class Response(AbstractResponse):
    """Sent synchronously, to confirm request
     __________          __________
    |          |        |          |
    |  Server  | <----- |  Client  |
    |__________|        |__________|

    """


class Result(AbstractResponse):
    """Sent asynchronously, with results from command
     __________          __________
    |          |        |          |
    |  Server  | -----> |  Client  |
    |__________|        |__________|

    """


@pifou.lib.log
class Server(object):

    commands = {}  # Executed commands
    clients = {}  # Connected clients
    queue = queue.Queue()  # Commands about to be executed

    def __init__(self, receiver):
        context = zmq.Context()
        incoming = context.socket(zmq.REP)

        self.incoming = incoming
        self.context = context
        self.receiver = receiver

        self.listen()

    def listen(self):
        self.incoming.bind("tcp://*:6000")

        def process_incoming():
            while True:
                message = self.incoming.recv_json()
                command = message['command']
                command_obj = COMMANDS[command].from_message(message)

                if command == 'connect':
                    command_obj.receiver = self

                else:
                    command_obj.receiver = self.receiver

                # Queue command
                self.queue.put(command_obj)

                response = Result(status='ok')
                message = response.to_message()
                self.incoming.send_json(message)

        # Start receiver

        receiver_thread = threading.Thread(target=process_incoming)
        receiver_thread.daemon = True
        receiver_thread.start()
        self.log.info("    Server started")

        # Start worker

        worker_thread = threading.Thread(target=self.worker)
        worker_thread.daemon = True
        worker_thread.start()
        self.log.info("    Worker started")

    def worker(self):
        """This function is in charge of execution ordering.

        It makes sure that commands are executed in the order that
        they are received; regardless of them being either synchronous
        or asynchronous.

        """

        while True:
            command = self.queue.get(block=True)

            message = {'status': 'fail', 'result': None}

            try:
                message['result'] = command.do()

            except Exception as e:
                message['error'] = str(e)

            self.queue.task_done()

    def execute(self, command):
        self.log.info("    Executing command: %s" % command)
        return command.do()

    def stop(self):
        self.incoming.close()
        print "Server stopped"

    def register(self, endpoint):
        # endpoint = "tcp://{ip}:{port}".format(ip=ip, port=port)

        if not endpoint in self.clients:
            channel = self.context.socket(zmq.REQ)
            self.log.info("Connecting to client @ %s" % endpoint)
            # channel.connect(endpoint)
            self.log.info("Connected")

            self.clients[endpoint] = channel
            self.log.info("%s registered" % endpoint)
        else:
            self.log.warning("%s already registered" % endpoint)


class Signature(Exception):
    """Raised when there is an error in the argument signature"""
    pass


def name_from_command(command):
    if hasattr(command, '__name__'):
        base = command
    else:
        base = command.__class__
    return base.__name__.rsplit("Command", 1)[0].lower()


class AbstractCommand(Request):
    """Abstract base class for all commands

    Differences between zerocommand:
        Here, we instantiate commands prior to sending them across
        the network. Commands are marshalled and unmarshalled and
        finally executed.

        This means that commands contain not only their target
        receiver and state, but also each argument used in the
        execution.

            >>> command.do()
            # Arguments are given prior to running do()

        The benefit is that the server may call upon do(), without
        knowing which arguments it takes or what it will do.

        Another benefit is that we may use command objects as a means
        of checking that we pass along the appropriate signature, prior
        to sending the command:

            >>> {'command': 'load', 'blocking': False}
            # Here, the signature is wrong, but we won't know until
            #

    """

    blocking = False

    def __init__(self, receiver=None):
        self.receiver = receiver
        self.state = {}

    def to_message(self):
        return {
            'command': name_from_command(self),
            'blocking': self.blocking
        }

    def do(self, *args):
        return


class ConnectCommand(AbstractCommand):
    def __init__(self, endpoint=None, *args, **kwargs):
        super(ConnectCommand, self).__init__(*args, **kwargs)
        self.endpoint = endpoint

    def do(self):
        self.receiver.register(self.endpoint)

    @classmethod
    def from_message(cls, message):
        return cls(endpoint=message['endpoint'])

    def to_message(self):
        message = super(ConnectCommand, self).to_message()
        message.update({'endpoint': self.endpoint})
        return message


class ImportCommand(AbstractCommand):
    def __init__(self, path=None, *args, **kwargs):
        super(ImportCommand, self).__init__(*args, **kwargs)
        self.path = path

    def do(self):
        if not self.receiver:
            raise Incomplete("Command has no receiver")

        return self.receiver.import_file(path=self.path)

    @classmethod
    def from_message(cls, message):
        return cls(path=message['path'])

    def to_message(self):
        message = super(ImportCommand, self).to_message()
        message.update({'path': self.path})
        return message


class ReferenceCommand(AbstractCommand):
    def do(self):
        return self.receiver.import_reference(path=self.path)


COMMANDS = {}
for command in (ConnectCommand,
                ImportCommand,
                ReferenceCommand):
    COMMANDS[name_from_command(command)] = command
