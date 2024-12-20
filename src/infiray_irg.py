from PIL import Image
import warnings
import numpy as np
import struct
import io

__version__ = "1.3.0"

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
    flag0, _unk1, _zero1, fine_offset, _unk2, jpeg_length,\
    y_res_2, x_res_2, _unk3, = struct.unpack('<HIHHHHHHHIHHI', header[2:34])

    fine_temp_offset1, fine_temp_offset2, *rest, high_gain_mode_flag = struct.unpack('<11I', header[34:78])
    
    if fine_temp_offset1 != fine_temp_offset2:
        warnings.warn(f'File lists two different zero offsets for the fine image data {fine_temp_offset1} and {fine_temp_offset2}. Resulting radiometric data might be offset. Please report this with an example file to code@jaseg.de.')

    fine_temp_offset = fine_temp_offset1 / 10000

#    import textwrap
#    print(textwrap.dedent(f'''
#        {_unk0=}, {coarse_section_length=}, {y_res=}, {x_res=},
#        {flag0=}, {_unk1=}, {_zero1=}, {fine_offset=}, {_unk2=}, {jpeg_length=},
#        {y_res_2=}, {x_res_2=}, {_unk3=}
#        {fine_temp_offset1=} {fine_temp_offset1=} {rest=}, {high_gain_mode_flag=}'''))

    if x_res*y_res != coarse_section_length:
        raise ValueError('Resolution mismatch in header')
        
    vis_jpg = None
    if model == 'c201':
        if header[-2:] != bytes([0xac,0xca]):
            raise ValueError(f'Header end marker not found. Got header: {header[-2]:02x} {header[-1]:02x}')
        coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
        fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))

        if flag0 == 1: # Seen in Autel Robotics Evo II Dual 640T V3 file
            fine_img = (fine_img / 64) - fine_temp_offset

        else: # C201 files
            # 1/16th Kelvin steps
            fine_img = (fine_img / 16) - fine_temp_offset

        if jpeg_length > 0:
            # I have seen a file from an Autel Robotics Evo II Dual 640T V3 that looks like a C201 file, but lacks the
            # visible data.
            vis_jpg = Image.open(io.BytesIO(consume(jpeg_length)))

    elif model == 'other':
        if header[-2:] != bytes([0xab,0xba]):
            raise ValueError(f'Header end marker not found. Got header: {header[-2]:02x} {header[-1]:02x}')
        coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
        # 0.1 Kelvin steps
        fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))
        fine_img = fine_img / 10 - fine_temp_offset

        vis_jpg = Image.open(io.BytesIO(data))

    else:
        header += consume(128)
        coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
        fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))
        fine_img = fine_img / 10 - fine_temp_offset

        # In my example file, data now contains the JSON '{"roi":[]}' and no JPG. We ignore that.
    
    return coarse_img, fine_img, vis_jpg

