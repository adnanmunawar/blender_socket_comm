import socket
import time


class UserServer:
    def __init__(self):
        # Globals
        self.server_addr = ''
        self.server_port = 3004
        self.server = None
        self.client = None

    def create_server(self, addr=None, port=None):
        if addr is not None:
            self.server_addr = addr

        if port is not None:
            self.server_port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.server_addr, self.server_port))
        self.server.listen(1)
        print('Waiting For Connection on: ', self.server_addr, ':', self.server_port)
        self.client, client_addr = self.server.accept()
        print('Connected To: ', client_addr)

    def set_vtx_pos(self, idx, x, y, z):
        packet = str(idx) + ',' + str(x) + ',' + str(y) + ',' + str(z)
        self.client.send(packet.encode())

    def get_vtx_pos(self, idx):
        pass

server = UserServer()
server.create_server(port=3002)
