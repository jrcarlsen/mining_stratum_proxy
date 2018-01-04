################################################################################

class Monitor:
    def cmd_connections(client, cmd):
        client.client.send('connected clients: %i\n' % len(client.server.clients))

    def cmd_quit(client, cmd):
        client.client.disconnect()

    def cmd_noop(self, client, cmd):
        return

################################################################################

m = Monitor()

cmd_map = {
    'connections':  m.cmd_connections,
    'quit':         m.cmd_quit,
    '':             m.cmd_noop,
}

################################################################################

