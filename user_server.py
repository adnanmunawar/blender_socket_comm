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

    def get_vtx_count(self):
        packet = GET_VTX_COUNT
        self.client.send(packet.encode())

        packet = self.client.recv(1024)
        packet = packet.decode()
        # print(packet)

        if packet.find(GET_VTX_COUNT) == 0:
            data = packet.split(GET_VTX_COUNT)[1]
            v = unpack_vector(data, GET_VTX_COUNT_VEC_SIZE)

        return int(v[0])

    def get_vtx_pos(self, idx):
        data = pack_vector([idx])
        packet = GET_VTX_POS + data
        self.client.send(packet.encode())

        packet = self.client.recv(1024)

        packet = packet.decode()
        # print(packet)

        if packet.find(GET_VTX_POS) == 0:
            data = packet.split(GET_VTX_POS)[1]
            v = unpack_vector(data, GET_VTX_POS_VEC_SIZE)

        return v

    def test_sin_wave_equation(self):

        vtx_count = self.get_vtx_count()
        n_x_vtx = int(math.sqrt(vtx_count))
        n_y_vtx = int(math.sqrt(vtx_count))

        print("Vertex Count: ", vtx_count)

        z_start = 0.0

        start_time = time.time()

        for x in range(0, n_x_vtx):
            for y in range(0, n_y_vtx):
                t = time.time() - start_time
                idx = x*n_x_vtx + y
                i, xp, yp, zp = self.get_vtx_pos(idx)
                if idx % 10 == 0:
                    percent_complete = 100 * (float(idx) / float(vtx_count))
                    print("Percent Complete, ", percent_complete)
                # print("Vtx Pos [", i, "] = ", xp, yp, zp, end="\r")
                mag_x = 3.0
                mag_y = 5.0
                zp = z_start + math.sin(mag_x*xp) + math.cos(mag_y*yp)
                self.set_vtx_pos(idx, xp, yp, zp)
                time.sleep(0.001)


us = UserServer()
us.create_server(port=3002)

time.sleep(1)
us.test_sin_wave_equation()
us.shutdown_server()

