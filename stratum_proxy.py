#!/usr/bin/env python
#
################################################################################

import time
import socket
import select

################################################################################

PORT = 6666

BACKEND_ADDRESS = "zec-eu1.nanopool.org"
BACKEND_PORT    = 6666 

DEBUG = False

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
        debug(self, "SETMODE %s" % mode)
        self.client.server.socket_setmode(self.socket, mode, self)

    def disconnect(self):
        debug(self, "DISCONNECT")
        assert(self.connected == True)
        self.socket_setmode(None)
        self.connected = False
        self.socket.close()
        self.socket = None

    def connect(self):
        debug(self, "CONNECT")
        assert(self.connected == False)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.addr)
        self.socket_setmode('r')
        self.connected = True        
    
    def event(self, event):
        if event & select.EPOLLIN:
            self.net_receive()
        elif event & select.EPOLLOUT:
            self.net_send()
        else:
            print "ERROR: Uknown event", self, event
            raise SystemExit

    def net_receive(self):
        data = self.socket.recv(4096)
        if not data:
            self.disconnect()
            return

        debug(self, "<<< %s" % data)
        self.buffer_in += data
        self.client.process_connections()

    def net_send(self):
        data = self.buffer_out[:4096]
        self.buffer_out = self.buffer_out[4096:]
        if not self.buffer_out:
            self.socket_setmode('r')
        if data:
            debug(self, ">>> %s" % data)
            self.socket.send(data)
        
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
        if self.backend.buffer_out != 0:
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
        self.socket.bind(('0.0.0.0', PORT))
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
        for client in self.clients:
            if client.retired():
                debug(self, "RETIRED %s" % client)
                del self.clients[client]

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

s = Server(PORT)

while True:
    s.sockets_poll(timeout=5)
    s.clients_cleanup()
    s.status()

################################################################################

