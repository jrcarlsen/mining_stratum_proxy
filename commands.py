def cmd_connections(client, cmd):
    client.client.send('connected clients: %i\n' % len(client.server.clients))

cmd_map = {
    'connections': cmd_connections,
}