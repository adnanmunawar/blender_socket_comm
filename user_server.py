import socket
import time
import math
from data_utils import *


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
        data = pack_vector([idx, x, y, z])
        packet = SET_VTX_POS + data
        self.client.send(packet.encode())

    def get_vtx_pos(self, idx):
        data = pack_vector([idx])
        packet = GET_VTX_POS + data
        self.client.send(packet.encode())

        packet = self.client.recv(1024)
        msg = packet.decode()
        print(msg)

    def test_sin_wave_equation(self):
        n_x_vtx = 9
        n_y_vtx = 9

        x_start = -1.0
        y_start = -1.0
        z_start = 0.0

        x_range = 1.0
        y_range = 1.0
        z_range = 1.0

        start_time = time.time()

        dx = x_range / (n_x_vtx - 1)
        dy = y_range / (n_y_vtx - 1)

        while time.time() - start_time < 5.0:
            for x in range(0, n_x_vtx):
                for y in range(0, n_y_vtx):
                    t = time.time() - start_time
                    xp = x_start + x*dx
                    yp = y_start + y*dy
                    zp = z_start + math.sin(t + dx + dy)
                    print('Vetrex No: ', x*n_x_vtx + y, end="\r")
                    self.set_vtx_pos(x + y*n_y_vtx, xp, yp, zp)
                    time.sleep(0.001)


us = UserServer()
us.create_server(port=3001)

time.sleep(1)
us.test_sin_wave_equation()
us.shutdown_server()

