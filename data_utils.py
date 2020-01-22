# GRAMMAR
DISCONNECT = ""
SET_VTX_POS = "SET_VTX_POS"
GET_VTX_POS = "GET_VTX_POS"

SET_VTX_POS_VEC_SIZE = 4
GET_VTX_POS_VEC_SIZE = 1


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
        v_str = data.split(',')
        if length != len(v_str):
            print('Warning! Required Length is not Equal to Actual Length')
        v = [float(v) for v in v_str]
    except ValueError:
        pass
    return v