import socket
import time

# Globals
server_addr = ''
server_port = 3004

def set_vtx_pos(idx, x, y, z):
    packet = str(idx) + ',' + str(x) + ',' + str(y) + ',' + str(z)
    client.send(packet.encode())

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((server_addr, server_port))
server.listen(1)
client, client_addr = server.accept()
print('Connected To: ', client_addr)
