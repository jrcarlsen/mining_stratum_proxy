#!/usr/bin/env python
#
################################################################################

import socket
import select
import sys

################################################################################

BACKEND_ADDRESS = "eu1.miningpool.shop"
BACKEND_PORT    = 3533

LISTEN_PORT = int(sys.argv[1])

DEBUG = True

################################################################################

def debug(source, text):
    if DEBUG:
        print source, text

################################################################################

class Connection:
    buffer_in = ''
    buffer_out = ''

    def __init__(self, client, socket_accept=None):
        self.client = client
        if socket_accept:
            self.socket, self.addr = socket_accept
            self.connected = True
            debug(self, "CONNECTED")
            self.socket_setmode('r')
        else:
            self.addr = (BACKEND_ADDRESS, BACKEND_PORT)
            self.socket = None
            self.connected = False

    def __repr__(self):
        if self.socket:
            fileno = self.socket.fileno()
        else:
            fileno = -1
        return "<Connection fileno='%i' addr='%s' buffer_in='%i' buffer_out='%i'>" % (
            fileno, self.addr, len(self.buffer_in), len(self.buffer_out))

    def socket_setmode(self, mode):
        """Configure which events we want to get"""
        debug(self, "SETMODE %s" % mode)
        self.client.server.socket_setmode(self.socket, mode, self)

    def disconnect(self):
        """Disconnect the current connection"""
        assert(self.connected == True)
        debug(self, "DISCONNECT")
        self.socket_setmode(None)
        self.connected = False
        self.socket.close()
        self.socket = None

    def connect(self):
        """Establish the connection"""
        assert(self.connected == False)
        debug(self, "CONNECT")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect(self.addr)
        except socket.error:
            debug(self, "CONNECT FAILED")
            self.disconnect()
            return

        self.socket_setmode('r')
        self.connected = True        
    
    def event(self, event):
        # EPOLLIN events goes to the net_receive function
        if event & select.EPOLLIN:
            self.net_receive()
        # EPOLLOUT events goes to the net_send function
        if event & select.EPOLLOUT:
            self.net_send()

    def net_receive(self):
        # If there is data to from the network, read up to 4096 bytes of it
        data = self.socket.recv(4096)

        # If there is no data, it means we got disconnected
        if not data:
            self.disconnect()
            return

        # Add the data to our input buffer
        debug(self, "<<< %s" % data)
        self.buffer_in += data

        # Scan the input buffer to see if we got any complete commands yet
        self.client.process_connections()

    def net_send(self):
        # If there is data in the out buffer, send 4096 bytes of it
        data = self.buffer_out[:4096]
        self.buffer_out = self.buffer_out[4096:]
        if data:
            debug(self, ">>> %s" % data)
            self.socket.send(data)

        # If there is no more data to send, we only want to be informed of read events
        if not self.buffer_out:
            self.socket_setmode('r')
        
    def send(self, data):
        self.buffer_out += data
        if not self.connected:
            self.connect()
        self.socket_setmode('rw')

    def parse_buffer(self):
        lines = self.buffer_in.split('\n')
        if len(lines) == 1:
            return []
        self.buffer_in = lines[-1]
        return lines[:-1]

################################################################################

class Client:
    def __init__(self, server):
        self.server  = server
        self.client  = Connection(self, server.socket.accept()) 
        self.backend = Connection(self)

    def retired(self):
        if self.client.connected:
            return False
        if len(self.backend.buffer_out) != 0:
            return False
        return True

    def process_connections(self):
        lines = self.client.parse_buffer()
        for line in lines:
            self.backend.send(line+'\n')
        
        lines = self.backend.parse_buffer()
        for line in lines:
            self.client.send(line+'\n')

        if not self.backend.connected:
            self.backend.connect()

################################################################################

class Server:
    sockets = {}
    clients = {}
    connected = True
    epoll = select.epoll()

    def __init__(self, port):
        # Create a Server Socket for incoming connections
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', port))
        self.socket.listen(1)
        self.socket.setblocking(0)

        # Register our socket
        self.socket_setmode(self.socket, 'r', self)

    def __repr__(self):
        return "<Server fileno='%i', clients='%i'>" % (self.socket.fileno(), len(self.clients))

    def socket_setmode(self, socket, mode, callback_obj):
        if not mode:
            del self.sockets[socket.fileno()]
            self.epoll.unregister(socket.fileno())
            return

        modes = {
            'r': select.EPOLLIN,
            'rw': select.EPOLLIN + select.EPOLLOUT,
        }

        if not self.sockets.has_key(socket.fileno()):
            self.sockets[socket.fileno()] = callback_obj
            self.epoll.register(socket.fileno(), modes[mode])
        else:
            self.sockets[socket.fileno()] = callback_obj
            self.epoll.modify(socket.fileno(), modes[mode])

    def sockets_poll(self, timeout):
        events = self.epoll.poll(timeout)
        for fileno, event in events:
            assert(self.sockets.has_key(fileno) == True)
            self.sockets[fileno].event(event)

    def clients_cleanup(self):
        for client in list(self.clients):
            if client.retired():
                debug(self, "RETIRED %s" % client)
                # Delete the connections from the client
                del self.sockets[client.backend.fileno()]
                del self.sockets[client.client.fileno()]
                # Remove the client from our client list
                del self.clients[client]
                del client

    def event(self, event):
        assert(event == 1)
        client = Client(self)
        self.clients[client] = True

    def status(self):
        for c in self.clients:
            print "[32mC ", c
            print " => client:  ", c.client
            print " => backend: ", c.backend
        print "[0m"

################################################################################

s = Server(LISTEN_PORT)

while True:
    s.sockets_poll(timeout=5)
    s.clients_cleanup()
    s.status()

################################################################################

