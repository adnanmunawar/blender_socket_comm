# Author: Adnan Munawar
# Email: amunawa2@jh.edu
# Lab: LCSR

bl_info = {
    "name": "Socket Client for Blender",
    "author": "Adnan Munawar",
    "version": (0, 1),
    "blender": (2, 81, 0),
    "location": "View3D > Tool > SocketClient",
    "description": "",
    "warning": "",
    "wiki_url": "https://github.com/adnanmunawar/blender_socket_comm",
    "category": "SocketClient",
}

import bpy
from bpy.props import StringProperty, IntProperty
import socket
import threading
from collections import Counter
import time
from _collections import deque
import functools
import numpy as np
import os

# Globals
server_addr = ''
server_port = 3004
client = None
rx_handle = None


class ConfigSB():
    def __init__(self, type):
        self.type = ''
        self.meshes_path = ''
        self.vtx_pos_queue = deque()
        self.thread_handle = None
        self.exit_thread = False
        self.sb_object = None

      
class ConfigGlobal():
    def __init__(self):
        self.mapping_filepath = ''
        self.max_frames_to_load = 300
        self.sb_config_list = None
        self.mapping = None


config_global = ConfigGlobal()
config_global.sb_config_list = [ConfigSB('Simulator'), ConfigSB('Network')]

# GRAMMAR
DISCONNECT = ""
SET_VTX_POS = "SET_VTX_POS"
SET_OBJ_POSE = "SET_OBJ_POSE"
GET_VTX_POS = "GET_VTX_POS"
GET_VTX_COUNT = "GET_VTX_COUNT"

SET_VTX_POS_VEC_SIZE = 4
SET_OBJ_POSE_VEC_SIZE = 6
GET_VTX_POS_VEC_SIZE = 1
GET_VTX_COUNT_VEC_SIZE = 1

data_queue = deque()
callback_idx = 0
th_handle = None
th2_handle = None
exit_thread = False
exit_thread2 = False
update_handle = []
update_handle_2 = []


########
def load_from_folder():
    global config_global
    config_global.mapping = np.genfromtxt(config_global.mapping_filepath)
    mapping = config_global.mapping
    for sc in config_global.sb_config_list:
        
        files_list = sorted(os.listdir(sc.meshes_path))
        frame_load_counter = 0
        print('Max Frames To Load: ', config_global.max_frames_to_load)
        for file in files_list:
            if frame_load_counter >= config_global.max_frames_to_load:
                break
            net_mesh = np.genfromtxt(sc.meshes_path + file)
            for i in range(len(mapping)):
                ni = int(mapping[i][0])  # Network Vertex Index
                bi = int(mapping[i][1])  # Blender Vertex Index
                sc.vtx_pos_queue.append([bi, net_mesh[ni, 0], net_mesh[ni, 1], net_mesh[ni, 2], frame_load_counter])
#            time.sleep(0.01)
            frame_load_counter = frame_load_counter + 1
        print('For File: ', sc.type, '. No. of Frames Loaded: ', frame_load_counter)


def load_vtx_positions():
    global th2_handle
    th2_handle = threading.Thread(target=load_from_folder)
    th2_handle.start()


##########


def pack_vector(vec, precission=3):
    vec_rounded = [round(v, precission) for v in vec]
    data = '('
    idx = 0
    size = len(vec_rounded)
    for v in vec_rounded:
        data = data + str(v)
        idx = idx + 1
        if idx < size:
            data = data + ','
    data = data + ')'
    return data


def unpack_vector(data, length=1):
    v = None
    try:
        items = data[data.find("(") + 1:data.find(")")]
        v_str = items.split(',')
        if length != len(v_str):
            print('Warning! Required Length is not Equal to Actual Length')
        v = [float(v) for v in v_str]
    except ValueError:
        pass
    return v


def connect(addr=None, port=None):
    global server_addr, server_port, client
    global client_rx, th_handle, exit_thread
    if addr is not None:
        server_addr = addr
    if port is not None:
        server_port = port

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((server_addr, server_port))
        client.setblocking(False)
        exit_thread = False
        th_handle = threading.Thread(target=client_rx)
        th_handle.start()
    except socket.error:
        client = None
        pass


def disconnect():
    global client, exit_thread, th_handle
    global update_handle
    print('Disconnect Called')
    if client:
        for h in update_handle:
            if bpy.app.timers.is_registered(h):
                bpy.app.timers.unregister(h)
        print('Closing Client', client)
        exit_thread = True
        client.close()
        client = None


def stop_visualization():
    global update_handle_2
    print('Stop Called')
    print('Emptying Vertex Position Queue')
    global config_global
    config_global.sb_config_list[0].vtx_pos_queue.clear()
    config_global.sb_config_list[1].vtx_pos_queue.clear()
    
    for h in update_handle_2:
        if bpy.app.timers.is_registered(h):
            bpy.app.timers.unregister(h)
            print('Stopping Visual Update')


def set_vtx_pos(obj, idx, x, y, z):
    if obj:
        # print('MOVING VTX(', idx, ') : ', x, y, z)
        num_vtx = len(obj.data.vertices)
        if 0 <= idx < num_vtx:
            idx = int(idx)
            obj.data.vertices[idx].co = (x, y, z)
        else:
            print('Error, Vtx Idx Invalid')


def set_obj_pose(obj, x, y, z, ro, pi, ya):
    if obj:
        obj.matrix_world.translation = (x, y, z)
        obj.rotation_euler = (ro, pi, ya)


def get_vtx_count(obj):
    global client
    if client:
        if obj:
            vtx_count = [len(obj.data.vertices)]
        else:
            print('Error, No Active Object')
            vtx_count = [-1]

        data = pack_vector(vtx_count)
        packet = GET_VTX_COUNT + data
        client.send(packet.encode())


def get_vtx_pos(obj, idx):
    global client
    if client:
        if obj:
            # print('MOVING VTX(', idx, ') : ', x, y, z)
            vtx_count = len(obj.data.vertices)
            if 0 <= idx < vtx_count:
                pos = obj.data.vertices[idx].co
                vec = [idx, pos[0], pos[1], pos[2]]
            else:
                print('Error, Vtx Idx Invalid')
                vec = [-1, 999, 999, 999]

            data = pack_vector(vec)
            packet = GET_VTX_POS + data
            client.send(packet.encode())


def client_rx(args=None):
    global data_queue, client, exit_thread
    while not exit_thread:
        try:
            packet = client.recv(1024)
            packet = packet.decode()
            data_queue.append(packet)
        except socket.error:
            pass
        time.sleep(0.0005)


def timer_update_func(object):
    global data_queue, callback_idx
    callback_idx = callback_idx + 1

    # Address a max of n request per call
    max_reqs = 30

    if callback_idx % max_reqs == 0:
        print(callback_idx, ') ', len(data_queue))

    ee_obj = bpy.context.scene.network_ee_object
    sb_obj = bpy.context.scene.network_sb_object

    while max_reqs:
        try:
            msg = data_queue.popleft()
            if msg == DISCONNECT:
                disconnect()
            elif msg == GET_VTX_COUNT:
                get_vtx_count(sb_obj)
            elif msg.find(GET_VTX_POS) == 0:
                data = msg.split(GET_VTX_POS)[1]
                idx = unpack_vector(data, GET_VTX_POS_VEC_SIZE)
                idx = int(idx[0])
                get_vtx_pos(sb_obj, idx)
            elif msg.find(SET_VTX_POS) == 0:
                data = msg.split(SET_VTX_POS)[1]
                idx, x, y, z = unpack_vector(data, SET_VTX_POS_VEC_SIZE)
                set_vtx_pos(sb_obj, idx, x, y, z)
            elif msg.find(SET_OBJ_POSE) == 0:
                data = msg.split(SET_OBJ_POSE)[1]
                x, y, z, ro, pi, ya = unpack_vector(data, SET_OBJ_POSE_VEC_SIZE)
                set_obj_pose(ee_obj, x, y, z, ro, pi, ya)

        except IndexError:
            break
        max_reqs = max_reqs - 1
    return 0.005


def visualize_from_vtx_queue(context):
    global config_global
    # max of n request per call
    vpf = context.scene.vpf
    while vpf:
        try:
            for sc in config_global.sb_config_list:
                msg = sc.vtx_pos_queue.popleft()
                set_vtx_pos(sc.sb_object, msg[0], msg[1], msg[2], msg[3])
                context.scene.simulating_frame_num = msg[4]
        except IndexError:
            break
        vpf = vpf - 1
    return 0.005


class ConnectOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.socket_connect_operator"
    bl_label = "Connect To Server"

    def execute(self, context):
        global rx_handle, update_handle
        if client is None:
            connect(context.scene.server_addr, context.scene.server_port)
            for i in range(0, 1):
                fn = functools.partial(timer_update_func, bpy.context.object)
                bpy.app.timers.register(fn)
                update_handle.append(fn)

        return {'FINISHED'}


class DisconnectOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.socket_disconnect_operator"
    bl_label = "Disconnect"

    def execute(self, context):
        disconnect()
        return {'FINISHED'}


class RunMeshesVisualizationOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.run_meshes_visualization_operator"
    bl_label = "Visualize"

    def execute(self, context):
        
        global config_global
        
        config_global.mapping_filepath = bpy.path.abspath(context.scene.mapping_filepath)
        config_global.max_frames_to_load = context.scene.max_frames_to_load
        
        sb_list = config_global.sb_config_list
        
        sb_list[0].sb_object = bpy.context.scene.simulator_sb_object
        sb_list[0].meshes_path = bpy.path.abspath(context.scene.simulator_meshes_path)
        
        sb_list[1].sb_object = bpy.context.scene.network_sb_object 
        sb_list[1].meshes_path = bpy.path.abspath(context.scene.network_meshes_path)
        
        simulator_update_frames_dir(self, context)
        network_update_frames_dir(self, context)
        
        if len(sb_list[0].vtx_pos_queue) > 0 or len(sb_list[1].vtx_pos_queue) > 0:
            print('Patience child! Queue is not empty yet')
            print('Either press stop first, or wait for the queue to empty itself')
        else:
            load_vtx_positions()
            fn = functools.partial(visualize_from_vtx_queue, context)
            bpy.app.timers.register(fn)
            update_handle_2.append(fn)
                
        return {'FINISHED'}

  
def simulator_update_frames_dir(self, context):
    global config_global
    sb_conf = config_global.sb_config_list[0]
    sb_conf.meshes_path = bpy.path.abspath(context.scene.simulator_meshes_path)
    files_list = sorted(os.listdir(sb_conf.meshes_path))
    context.scene.simulator_num_frames_found = len(files_list)

  
def network_update_frames_dir(self, context):
    global config_global
    sb_conf = config_global.sb_config_list[1]
    sb_conf.meshes_path = bpy.path.abspath(context.scene.network_meshes_path)
    files_list = sorted(os.listdir(sb_conf.meshes_path))
    context.scene.network_num_frames_found = len(files_list)


class StopVisualizationOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scene.stop_visualization_operator"
    bl_label = "Stop"

    def execute(self, context):
        stop_visualization()
        return {'FINISHED'}


class BlenderClientPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Blender Client Panel"
    bl_idname = "Blender_PT_Client"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SocketClient"

    bpy.types.Scene.server_addr = StringProperty(name="Server Addr", default="localhost", description="Server Addr")
    bpy.types.Scene.server_port = IntProperty(name="Server Port", default=3001, description="Server Port")
    bpy.types.Scene.vpf = IntProperty(name="Vtx Per Frame", default=100, min=0, description="No. of Vertex Per Iteration")
    bpy.types.Scene.max_frames_to_load = IntProperty(name="Max Load Frames", default=300, min=0, description="No. of frames to load")
    bpy.types.Scene.simulating_frame_num = IntProperty(name="Simulating Frame No.", default=0, description="Simulating Frame No.")
    
    bpy.types.Scene.simulator_num_frames_found = IntProperty(name="Simulator Frames Found", default=0, description="No. of simulator frames found")
    bpy.types.Scene.simulator_ee_object = bpy.props.PointerProperty(name="Simulator End-Effector", type=bpy.types.Object)
    bpy.types.Scene.simulator_sb_object = bpy.props.PointerProperty(name="Simulator Soft Body", type=bpy.types.Object)
    
    bpy.types.Scene.network_num_frames_found = IntProperty(name="Network Frames Found", default=0, description="No. of network frames found")
    bpy.types.Scene.network_ee_object = bpy.props.PointerProperty(name="Network End-Effector", type=bpy.types.Object)
    bpy.types.Scene.network_sb_object = bpy.props.PointerProperty(name="Network Soft Body", type=bpy.types.Object)

    bpy.types.Scene.mapping_filepath = bpy.props.StringProperty \
            (
            name="Mapping Filepath",
            default="",
            description="Define the Mapping file",
            subtype='FILE_PATH'
        )

    bpy.types.Scene.simulator_meshes_path = bpy.props.StringProperty \
            (
            name="Simulator Meshes Path (Dir)",
            default="",
            description="Define the path to the meshes file",
            subtype='DIR_PATH',
            update=simulator_update_frames_dir
        )

    bpy.types.Scene.network_meshes_path = bpy.props.StringProperty \
            (
            name="Network Meshes Path (Dir)",
            default="",
            description="Define the path to the meshes file",
            subtype='DIR_PATH',
            update=network_update_frames_dir
        )

    def draw(self, context):
        global client
        layout = self.layout

        row = layout.row()
        row.label(text="Blender Client!", icon='WORLD_DATA')

        box = layout.box()
        col = box.column()
        col.prop_search(context.scene, "simulator_ee_object", context.scene, "objects")

        col = box.column()
        col.prop_search(context.scene, "simulator_sb_object", context.scene, "objects")

        box = layout.box()
        col = box.column()
        col.prop_search(context.scene, "network_ee_object", context.scene, "objects")

        col = box.column()
        col.prop_search(context.scene, "network_sb_object", context.scene, "objects")

        row = layout.row()
        row.prop(context.scene, 'server_addr')

        row = layout.row()
        row.prop(context.scene, 'server_port')

        row = layout.row()
        row.enabled = not bool(client)
        row.operator('scene.socket_connect_operator')

        row = layout.row()
        row.enabled = bool(client)
        row.operator('scene.socket_disconnect_operator')

        col = layout.column()
        col.prop(context.scene, 'mapping_filepath')

        box = layout.box()
        col = box.column()
        col.prop(context.scene, 'simulator_meshes_path')

        col = box.column()
        col.prop(context.scene, 'simulator_num_frames_found')
        col.enabled = False

        box = layout.box()
        col = box.column()
        col.prop(context.scene, 'network_meshes_path')

        col = box.column()
        col.prop(context.scene, 'network_num_frames_found')
        col.enabled = False

        col = layout.column()
        col.prop(context.scene, 'max_frames_to_load')

        col = layout.column()
        col.prop(context.scene, 'vpf')

        col = layout.column()
        col.operator('scene.run_meshes_visualization_operator')

        col = layout.column()
        col.operator('scene.stop_visualization_operator')
        
        col = layout.column()
        col.prop(context.scene, 'simulating_frame_num')
        col.enabled = False


classes = (ConnectOperator,
           DisconnectOperator,
           RunMeshesVisualizationOperator,
           StopVisualizationOperator,
           BlenderClientPanel)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    # ungregister()
