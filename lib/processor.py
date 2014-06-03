

# def init(exchange, receiver):
#     in_message = exchange['in']
#     command, args, kwargs = (in_message['command'],
#                              in_message.get('args', []),
#                              in_message.get('kwargs', {}))

#     out_message = {'status': 'fail'}

#     if command == 'clients':
#         out_message['result'] = receiver.clients.keys()
#         out_message['status'] = 'ok'

#     elif command == 'connect':
#         endpoint = args[0]
#         if not endpoint in receiver.clients:
#             channel = receiver.context.socket(zmq.REQ)
#             channel.connect(endpoint)

#             receiver.clients[endpoint] = channel
#             receiver.log.info("%s registered" % endpoint)
#         else:
#             receiver.log.warning("%s already registered" % endpoint)



# def command(exchange):
#     while True:
#         in_message = self.command_channel.recv()

#         # Deconstruct in_message
#         #  _________
#         # |         |
#         # |  <~~~~  |
#         # |_________|

#         command = in_message[constant.COMMAND]
#         client_id = in_message[constant.ID]
#         args, kwargs = (in_message[constant.ARGS],
#                         in_message[constant.KWARGS])

#         # Prepare output
#         #  __________
#         # |          |
#         # |   ~~~>   |
#         # |__________|

#         out_message = {constant.STATUS: constant.FAIL}

#         try:
#             command_cls = COMMANDS[command]
#         except KeyError:
#             out_message[constant.INFO] = "%r not available" % command

#         else:
#             # Command OK
#             #  ___________
#             # |           |
#             # |  command  |
#             # |___________|

#             kwargs['receiver'] = self.receiver
#             command_inst = command_cls(*args, **kwargs)

#             try:
#                 channel = self.clients[client_id]
#             except KeyError:
#                 out_message[constant.INFO] = ("%s not registered, "
#                                              "try reconnecting.." %
#                                              client_id)
#             else:
#                 # Client OK
#                 #  ___________
#                 # |           |
#                 # |   client  |
#                 # |___________|

#                 item = (command_inst,
#                         channel)

#                 # Queue request
#                 self.log.info("Storing %r in queue" % command)
#                 self.queue.put(item)
#                 self.log.info("Stored")

#                 out_message[constant.STATUS] = constant.OK

#         # Prepare output
#         #  __________
#         # |          |
#         # |   --->   |
#         # |__________|

#         self.command_channel.recv_confirm(out_message)