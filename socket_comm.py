import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('',3001))
s.setblocking(False)
my_list = []

def rx(args):
    global my_list
    try:
        msg = s.recv(1024)
        msg = msg.decode()
        print(msg)
        my_list.append(msg)
        try:
            idx, x, y, z = msg.split(',')
            idx = int(idx)
            x = float(x)
            y = float(y)
            z = float(z)
            print('MOVING VTX(', idx, ') : ', x, y, z)
            if bpy.context.object:
                bpy.context.object.data.vertices[idx].co = (x,y,z)
        except ValueError:
            pass
    except socket.error:
        pass

bpy.app.handlers.scene_update_pre.append(rx)
