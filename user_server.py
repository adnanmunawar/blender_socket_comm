import socket
import time


class UserServer:
    def __init__(self):
        # Globals
        self.server_addr = ''
        self.server_port = 3001
        self.server = None
        self.client = None

    def create_server(self, addr=None, port=None):
        if addr is not None:
            self.server_addr = addr

        if port is not None:
            self.server_port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.server_addr, self.server_port))
        self.server.listen(1)
        print('Waiting For Connection on: ', self.server_addr, ':', self.server_port)
        self.client, client_addr = self.server.accept()
        print('Connected To: ', client_addr)

    def shutdown_server(self):
        print('Shutdown called on: ', self.server)
        if self.server:
            self.server.shutdown(socket.SHUT_RDWR)
            self.server.close()
            time.sleep(0.5)
            self.server = None
            print('Closed Server')

    def set_vtx_pos(self, idx, x, y, z):
        packet = str(idx) + ',' + str(x) + ',' + str(y) + ',' + str(z)
        self.client.send(packet.encode())

    def get_vtx_pos(self, idx):
        pass

us = UserServer()
us.create_server(port=3001)
time.sleep(3)
us.shutdown_server()

