import socket

# Globals
server_addr = ''
server_port = 3004

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((server_addr, server_port))
client.setblocking(False)

def client_rx(args):
    try:
        packet = client.recv(1024)
        packet = packet.decode()
        try:
            idx, x, y, z = packet.split(',')
            idx = int(idx)
            x = float(x)
            y = float(y)
            z = float(z)
            # print('MOVING VTX(', idx, ') : ', x, y, z)
            if bpy.context.object:
                bpy.context.object.data.vertices[idx].co = (x,y,z)
        except ValueError:
            pass
    except socket.error:
        pass

bpy.app.handlers.scene_update_pre.append(client_rx)
