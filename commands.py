################################################################################

class Monitor:
    def cmd_connections(self, client, cmd):
        client.client.send('connected clients: %i\n' % len(client.server.clients))

    def cmd_quit(self, client, cmd):
        client.client.disconnect()

    def cmd_fail(self, client, cmd):
        assert(1==2)

    def cmd_noop(self, client, cmd):
        return

################################################################################

m = Monitor()

cmd_map = {
    'connections':  m.cmd_connections,
    'quit':         m.cmd_quit,
    'fail':         m.cmd_fail,
    '':             m.cmd_noop,
}

################################################################################

