def cmd_connections(client, cmd):
    client.client.send('connected clients: %i\n' % len(client.server.clients))

def cmd_quit(client, cmd):
    client.client.disconnect()

cmd_map = {
    'connections':  cmd_connections,
    'quit':         cmd_quit,
}
