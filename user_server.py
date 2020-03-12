import os
import sys
import socket
import time
import math
import numpy as np
from data_utils import *
from random import random

#sys.path.insert(0,'../../deformable/')
#import utils

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

    def set_obj_pose(self, x, y, z, roll, pitch, yaw):
        data = pack_vector([x, y, z, roll, pitch, yaw])
        packet = SET_OBJ_POSE + data
        self.client.send(packet.encode())

    def get_vtx_count(self):
        packet = GET_VTX_COUNT
        self.client.send(packet.encode())

        packet = self.client.recv(1024)
        packet = packet.decode()
        # print(packet)
        time.sleep(0.5)
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

        mag_x = round((random() * 6), 2)
        mag_y = round((random() * 6), 2)

        for x in range(0, n_x_vtx):
            for y in range(0, n_y_vtx):
                t = time.time() - start_time
                idx = x*n_x_vtx + y
                i, xp, yp, zp = self.get_vtx_pos(idx)
                if idx % 10 == 0:
                    percent_complete = 100 * (float(idx) / float(vtx_count))
                    print("Percent Complete, ", percent_complete)
                # print("Vtx Pos [", i, "] = ", xp, yp, zp, end="\r")
                zp = z_start + (math.sin(mag_x*xp) + math.cos(mag_y*yp)) / 4
                self.set_vtx_pos(idx, xp, yp, zp)
                time.sleep(0.001)


    def surf_to_vol_map(idx, x, y, z):
        if idx < y*z:
            return idx
        else:
            idx 

    def play_simulation(self, mesh_path, mapping):
        mesh_files = os.listdir(mesh_path)
        mesh_files = sorted(mesh_files)
        for i in range(len(mesh_files)):
            cur_mesh_path = mesh_path + mesh_files[i]
            self.set_cube_vertices(cur_mesh_path, mapping)
            print(i)
            time.sleep(0.0001)
            
    def set_cube_vertices(self, mesh_path, mapping):
        mesh = np.genfromtxt(mesh_path)
        vtx_count = self.get_vtx_count()
#        print(vtx_count)
        for idx in range(vtx_count):
            cur_map = mapping[idx]
            cur_pt = mesh[cur_map[0]]
#            print(cur_pt)#, self.get_vtx_pos(cur_map[1]))
            self.set_vtx_pos(cur_map[1], cur_pt[0], cur_pt[1], cur_pt[2])
            time.sleep(0.0006)

    def make_mapping(self, mesh_path):
        mesh = np.genfromtxt(mesh_path)
        vtx_count = self.get_vtx_count()
        blender_mesh = np.zeros((vtx_count,3))
        for idx in range(vtx_count):
            pos = self.get_vtx_pos(idx)
            blender_mesh[idx] = [pos[1], pos[2], pos[3]]


        ind = np.lexsort((blender_mesh[:,2], blender_mesh[:,1], blender_mesh[:,0]))
        print(blender_mesh[ind][0:5])
        mapping = []
        i = 0
        for x in range(23):
            for y in range(12):
                for z in range(13):
                    if (x == 0) or (x == 22) or (y == 0) or (y == 11) or (z == 0) or (z == 12):
                        mapping = mapping + [i]
                    i = i + 1

        mapping = np.concatenate((np.array(np.expand_dims(mapping,1),dtype=np.int32), np.expand_dims(ind,1)), axis=1)
        np.savetxt('grid_order.txt',mapping,fmt='%i')


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Please enter at 2 arguments (first indicating use and second mesh path)')
        exit()
        
    us = UserServer()
    us.create_server(port=3002)
    mesh_path = sys.argv[2]
    mapping = np.loadtxt('grid_order.txt', dtype=np.int)
    if sys.argv[1] == 'show':
        us.set_cube_vertices(mesh_path, mapping)
    elif sys.argv[1] == 'map':
        us.make_mapping(mesh_path)
    elif sys.argv[1] == 'play':
        us.play_simulation(mesh_path, mapping)
    else:
        print('Unknown command in first argument')
#    mesh_path = sys.argv[1]
#    mesh_files = os.listdir(mesh_path)
#    mesh_files = sorted(mesh_files)

#    for i in range(len(mesh_files)):
#        mesh = np.genfromtxt(mesh_path + mesh_files[i])
#        us.set_cube_vertices(mesh)
#        time.sleep(1)
    us.shutdown_server()

