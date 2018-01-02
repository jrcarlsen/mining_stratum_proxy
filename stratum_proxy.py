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

################################################################################

class Client:
    def __init__(self, accept):
        self.socket, self.address = accept
        self.connected = True
        self.buffer = ''

    def __repr__(self):
        return "<Client fileno='%i', buffer_length='%i'>" % (self.socket.fileno(), len(self.buffer))

    def event(self, event):
        assert(event == 1)
        data = self.socket.recv(4096)
        if not data:
            self.connected = False
            return

        self.buffer += data
       
        
        

################################################################################

class Server:
    sockets = {}
    epoll = select.epoll()

    def __init__(self, port):
        # Create a Server Socket for incoming connections
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', PORT))
        self.socket.listen(1)
        self.socket.setblocking(0)

        # Register our socket
        self.socket_register(self.socket, self)
        #self.sockets[self.socket.fileno()] = self
        #self.epoll.register(self.socket.fileno(), select.EPOLLIN)

    def __repr__(self):
        return "<Server fileno='%i', clients='%i'>" % (self.socket.fileno(), len(self.sockets)-1)

    def socket_register(self, socket, obj):
        self.epoll.register(socket.fileno(), select.EPOLLIN)
        self.sockets[socket.fileno()] = obj

    def socket_unregister(self, socket):
        assert(self.sockets.has_key(socket.fileno()) == True)
        del self.sockets[socket.fileno()]
        self.epoll.unregister(socket.fileno()) 

    def check_sockets(self, timeout):
        events = self.epoll.poll(timeout)
        for fileno, event in events:
            assert(self.sockets.has_key(fileno) == True)
            self.sockets[fileno].event(event)

    def event(self, event):
        assert(event == 1)
        print "event"
        client = Client(self.socket.accept())
        self.socket_register(client.socket, client)

    def status(self):
        for s in self.sockets.values():
            print "!", s
        print

################################################################################

s = Server(PORT)

while True:
    s.check_sockets(timeout=3)
    s.status()

