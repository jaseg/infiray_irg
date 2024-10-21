from PIL import Image
import numpy as np
import struct
import io

def load(data):
    def consume(n):
        nonlocal data
        out, data = data[:n], data[n:]
        if len(out) < n:
            raise ValueError(f'File is truncated, tried to read {n} bytes, but only {len(out)} bytes remain.')
        return out

    header = consume(128)
    for model, match in {
            'c201': bytes([0xca, 0xac]),
            'other': bytes([0xba, 0xab]),
            'p200': bytes([0x04, 0xa0]),
            }.items():
        if (header[:2] + header[-2:]).startswith(match):
            break
    else:
        raise ValueError(f'Header magic not found. Got header: {header[0]:02x} {header[1]:02x}')

    _unk0, coarse_section_length, y_res, x_res,\
    _zero0, _unk1, _zero1, fine_offset, _unk2, jpeg_length,\
    y_res_2, x_res_2, _unk3, = struct.unpack('<HIHHHHHHHIHHI', header[2:34])

    _zero_celsius0, _zero_celsius1, *rest, high_gain_mode_flag = struct.unpack('<11I', header[34:78])
    
    import textwrap
    print(textwrap.dedent(f'''
        {_unk0=}, {coarse_section_length=}, {y_res=}, {x_res=},
        {_zero0=}, {_unk1=}, {_zero1=}, {fine_offset=}, {_unk2=}, {jpeg_length=},
        {y_res_2=}, {x_res_2=}, {_unk3=}
        {_zero_celsius0=} {_zero_celsius1=} {rest=}, {high_gain_mode_flag=}'''))

    if (x_res, y_res) != (x_res_2, y_res_2) and model != 'p200':
        raise ValueError(f'Resolution mismatch in header: {x_res}*{y_res} != {x_res_2}*{y_res_2}')

    if x_res*y_res != coarse_section_length:
        raise ValueError('Resolution mismatch in header')
        
    if model == 'c201':
        if header[-2:] != bytes([0xac,0xca]):
            raise ValueError(f'Header end marker not found. Got header: {header[-2]:02x} {header[-1]:02x}')
        coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
        # 1/16th Kelvin steps
        fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))
        fine_img = (fine_img / 16) - 273

        vis_jpg = Image.open(io.BytesIO(consume(jpeg_length)))

    elif model == 'other':
        if header[-2:] != bytes([0xab,0xba]):
            raise ValueError(f'Header end marker not found. Got header: {header[-2]:02x} {header[-1]:02x}')
        coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
        # 0.1 Kelvin steps
        fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))
        fine_img = fine_img / 10 - 273

        vis_jpg = Image.open(io.BytesIO(data))

    else:
        header += consume(128)
        coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
        fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))
        fine_img = fine_img / 10 - 273

        # In my example file, data now contains the JSON '{"roi":[]}' and no JPG. We ignore that.
        vis_jpg = None
    
    return coarse_img, fine_img, vis_jpg

