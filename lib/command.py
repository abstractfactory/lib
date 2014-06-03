"""
Who decides which command is associated with which receiver?
    At the moment, the receiver is attached on the server-end,
    with no hint coming from the client-side.

    Is it the clients responsibility to know which receiver
    to operate on?

"""

# standard library
import logging
import threading
import Queue as queue

# pifou library
import pifou.lib
import pifou.com.util
import pifou.com.error
import pifou.com.command
import pifou.com.constant
import pifou.com.pyzmq.endpoint

# pifou dependencies
import zmq

# local library
import lib

log = logging.getLogger()
if not log.handlers:
    lib.setup_log()

local_ip = pifou.com.util.local_ip()

# Shorthands
constant = pifou.com.constant
endpoint = pifou.com.pyzmq.endpoint


@pifou.lib.log
class Server(object):

    queue = queue.Queue()  # Commands about to be executed
    commands = dict()  # Executed commands
    clients = dict()  # Connected clients

    def __init__(self, receiver):
        self.receiver = receiver

        init_in = "tcp://*:7000"
        commands_in = "tcp://*:7001"
        commands_out = "tcp://localhost:7002"

        self.init_in = endpoint.create_consumer(init_in)
        self.commands_in = endpoint.create_consumer(commands_in)
        self.commands_out = endpoint.create_producer(commands_out)

        self.init_listen()
        self.commands_listen()

    def commands_listen(self):
        def process_command(in_message):
            """
                __________
               |          |
               |   /\/\   |
               |__________|

            """

            out_message = {constant.STATUS: constant.FAIL}

            client_id = in_message[constant.ID]
            commands_out = self.clients[client_id]

            command, args, kwargs = (
                in_message[constant.COMMAND],
                in_message.get(constant.ARGS, []),
                in_message.get(constant.KWARGS, {}))

            try:
                command_cls = COMMANDS[command]
            except KeyError:
                out_message[constant.INFO] = "%r not available" % command
                return out_message

            kwargs['receiver'] = self.receiver
            command_inst = command_cls(*args, **kwargs)

            # Store in queue
            #  _________
            # |         |
            # |    |    |
            # |    V    |
            # |_________|

            item = (command_inst,
                    commands_out)

            # Queue request
            self.log.info("Storing %r in queue" % command)
            self.queue.put(item)
            self.log.info("Stored")

            out_message[constant.STATUS] = constant.OK

            if command_inst.blocking is True:
                self.log.info("-|-  Blocking..")
                self.queue.join()
                self.log.info("---  Unblocking")

            return out_message

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

        # Start receiver
        receiver_thread = threading.Thread(target=thread,
                                           name='receiver_thread')
        receiver_thread.daemon = True
        receiver_thread.start()
        self.log.info("Listening on commands")

        # Start worker
        worker_thread = threading.Thread(target=self.worker,
                                         name='worker_thread')
        worker_thread.daemon = True
        worker_thread.start()
        self.log.info("Worker started")

    def init_listen(self):
        """Init channel"""

        def process_init(in_message):
            command, args, kwargs = (in_message[constant.COMMAND],
                                     in_message.get(constant.ARGS, []),
                                     in_message.get(constant.KWARGS, {}))

            out_message = {constant.STATUS: constant.FAIL}

            if command == 'clients':
                out_message[constant.RESULT] = self.clients.keys()
                out_message[constant.STATUS] = constant.OK

            elif command == 'connect':
                client = in_message[constant.ID]

                producer = endpoint.create_producer(client)
                self.clients[client] = producer

                info = "%s registered" % client
                out_message[constant.STATUS] = constant.OK
                out_message[constant.INFO] = info
                self.log.info(info)

            return out_message

        def thread():
            while True:
                #  __________
                # |          |
                # |   <---   |
                # |__________|
                in_message = self.init_in.recv_json()

                #  __________
                # |          |
                # |   /\/\   |
                # |__________|
                out_message = process_init(in_message)

                # Prepare output
                #  __________
                # |          |
                # |   --->   |
                # |__________|
                self.init_in.send_json(out_message)

        init_thread = threading.Thread(target=thread,
                                       name='init_thread')
        init_thread.daemon = True
        init_thread.start()
        self.log.info("Listening on init")

    def worker(self):
        """This function is responsible for the order of execution.
        _                                    _
        |  ___    ___    ___    ___          |
        | | 0 |  | 1 |  | 2 |  | 3 |         |
        | |___|  |___|  |___|  |___|         |
        |____________________________________|

        Both synchronous and asynchronous commands are stored
        in this queue.

        Note:
            This method can never fail. Failure is handled by client.

        """

        while True:
            command, commands_out = self.queue.get(block=True)

            # Prepare output
            #  __________
            # |          |
            # |   ~~~>   |
            # |__________|

            message = {constant.STATUS: constant.FAIL}

            # Execute command
            #  ___________
            # |           |
            # |    ...    |
            # |___________|

            self.log.info("Executing command.. %s" % command)

            try:
                return_value = command.do()
                message[constant.RESULT] = return_value
                message[constant.STATUS] = constant.OK
                self.log.info("Command executed")

            except Exception as e:
                message[constant.INFO] = str(e)
                self.log.error("Command failed")

            # Return value to client
            #  __________
            # |          |
            # |   --->   |
            # |__________|

            self.log.info("--> Returning results..")

            commands_out.send_json(message)

            # Await confirmation
            #  __________
            # |          |
            # |   <---   |
            # |__________|

            self.log.info("    Results returned, awaiting confirmation..")
            message = commands_out.recv_json()
            self.log.info("<-- Confirmation received")

            if message[constant.STATUS] != constant.OK:
                self.log.error("    Client reported failure")

            self.queue.task_done()

            if self.queue.empty():
                self.log.info("Queue is empty")

    def stop(self):
        self.incoming.close()
        print "Server stopped"


class ConnectCommand(pifou.com.command.AbstractCommand):
    def __init__(self, endpoint, *args, **kwargs):
        super(ConnectCommand, self).__init__(*args, **kwargs)
        self.endpoint = endpoint

    def do(self):
        self.receiver.register(self.endpoint)


class ImportCommand(pifou.com.command.AbstractCommand):
    def __init__(self, path, *args, **kwargs):
        super(ImportCommand, self).__init__(*args, **kwargs)
        self.path = path

    def do(self):
        if not self.receiver:
            raise pifou.com.error.Incomplete("Command has no receiver")

        return self.receiver.import_file(path=self.path)


class ReferenceCommand(pifou.com.command.AbstractCommand):
    def do(self):
        return self.receiver.import_reference(path=self.path)


COMMANDS = {}
for command in (
        ConnectCommand,
        ImportCommand,
        ReferenceCommand,
        pifou.com.command.TimeCommand,
        pifou.com.command.SleepCommand,
        ):

    COMMANDS[pifou.com.command.name(command)] = command
