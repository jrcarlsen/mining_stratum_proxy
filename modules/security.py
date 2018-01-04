################################################################################

class Blacklist:
    def __init__(self):
        pass

################################################################################

class Security:
    def __init__(self):
        self.blacklist = Blacklist()

    def client_connect(self, proxy):
        return self.blacklist.verifyproxy.client.addr[0]
        pass

    def client_check(self, proxy):
        pass

################################################################################
