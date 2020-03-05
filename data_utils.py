
# GRAMMAR
DISCONNECT = ""
SET_VTX_POS = "SET_VTX_POS"
SET_OBJ_POSE = "SET_OBJ_POSE"
GET_VTX_POS = "GET_VTX_POS"
GET_VTX_COUNT = "GET_VTX_COUNT"

SET_VTX_POS_VEC_SIZE = 4
SET_OBJ_POSE_VEC_SIZE = 6
GET_VTX_POS_VEC_SIZE = 4
GET_VTX_COUNT_VEC_SIZE = 1


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