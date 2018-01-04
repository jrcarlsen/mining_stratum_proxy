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

    def cmd_status(self, client, cmd):
        mesg = "PSProxy Status:\n"
        mesg += "Bytes in: 0\n"
        mesg += "Bytes out: 0\n"
        mesg += "Connections: %i\n" % len(client.server.clients)
        client.client.send(mesg)

    def cmd_show(self, proxy, cmd):
        if len(cmd) > 1:
            cmd_show = cmd[1]

        show_map = {
            'proxy': self.show_proxies,
            'proxies': self.show_proxies,
        }

        if not show_map.has_key(show_cmd):
            proxy.client.send('error in command: %s\n' % `show_cmd`)
            return

        show_map[show_cmd](proxy, cmd)

    def show_clients(self, proxy, cmd):
        for p in proxy.server.clients:
            proxy.client.send(`p`)

################################################################################

m = Monitor()

cmd_map = {
    'connections':  m.cmd_connections,
    'status':       m.cmd_status,
    'quit':         m.cmd_quit,
    'fail':         m.cmd_fail,
    '':             m.cmd_noop,
}

################################################################################

