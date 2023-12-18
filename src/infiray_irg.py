from PIL import Image
import numpy as np
import struct
import io

def load(data):
    def consume(n):
        nonlocal data
        out, data = data[:n], data[n:]
        if len(out) < n:
            raise ValueError('file is truncated')
        return out
        
    header = consume(128)
    if header[:2] != bytes([0xca, 0xac]) or header[-2:] != bytes([0xac, 0xca]):
        raise ValueError('Header magic not found.')

    _unk0, coarse_section_length, y_res, x_res,\
    _zero0, _unk1, _zero1, fine_offset, _unk2, jpeg_length,\
    y_res_2, x_res_2, _unk3, = struct.unpack('<HIHHHHHHHIHHI', header[2:34])

    _zero_celsius0, _zero_celsius1, *rest, high_gain_mode_flag = struct.unpack('<11I', header[34:78])
    
    if (x_res, y_res) != (x_res_2, y_res_2):
        raise ValueError(f'Resolution mismatch in header: {x_res}*{y_res} != {x_res_2}*{y_res_2}')

    if x_res*y_res != coarse_section_length:
        raise ValueError('Resolution mismatch in header')
        
    coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
    fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.int16).reshape((y_res, x_res))
    fine_img = (fine_img / 16) - 273
    vis_jpg = Image.open(io.BytesIO(consume(jpeg_length)))
    
    return coarse_img, fine_img, vis_jpg

