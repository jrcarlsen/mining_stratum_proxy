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
            'proxy': self.show_proxy,
            'proxies': self.show_proxy,
        }

        if not show_map.has_key(cmd_show):
            proxy.client.send('error in command: %s\n' % `cmd_show`)
            return

        show_map[cmd_show](proxy, cmd)

    def show_proxy(self, proxy, cmd):
        for p in proxy.server.clients:
            proxy.client.send(`p`+'\n')

################################################################################

m = Monitor()

cmd_map = {
    'connections':  m.cmd_connections,
    'status':       m.cmd_status,
    'quit':         m.cmd_quit,
    'fail':         m.cmd_fail,
    'show':         m.cmd_show,
    '':             m.cmd_noop,
}

################################################################################

