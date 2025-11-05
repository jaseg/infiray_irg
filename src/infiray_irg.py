from PIL import Image
import warnings
import numpy as np
import struct
import io

__version__ = "1.5.0"

def load(data, print_debug_information=False):
    def consume(n):
        nonlocal data
        out, data = data[:n], data[n:]
        if len(out) < n:
            raise ValueError(f'File is truncated, tried to read {n} bytes, but only {len(out)} bytes remain.')
        return out

    header = consume(4)
    _magic, header_len = struct.unpack('<HH', header)
    header += consume(header_len - 4)

    if print_debug_information:
        import binascii
        c200_reference_header = binascii.unhexlify('caac800000c000000001c00000008001000001c00001738300000001c0001c25000010a8290010a82900c4090000a00f000010270000000000001027000000000000000000000204000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000acca')
        print('[infiray_irg debug] Header hex:', binascii.hexlify(header).decode()[:512])
        print('[infiray_irg debug]  C200 diff:', ''.join(
            (f'\033[0m{b:02x}' if a == b else f'\033[91m{b:02x}') for a, b in zip(header, c200_reference_header)
            ) + '\033[0m')

    for model, match in {
            'c201': bytes([0xca, 0xac]),
            'other': bytes([0xba, 0xab]),
            'p200': bytes([0x04, 0xa0]),
            }.items():
        if (header[:2] + header[-2:]).startswith(match):
            break
    else:
        raise ValueError(f'Header magic not found. Got header: {header[0]:02x} {header[1]:02x}')

    coarse_section_length, y_res, x_res,\
    flag0, _unk1, _zero1, fine_offset, _unk2, jpeg_length,\
    y_res_2, x_res_2, emissivity = struct.unpack('<IHHHHHHHIHHI', header[4:34])
    emissivity /= 1e4

    # unit_flag indicates which temperature unit the UI was using. It does not seem to affect the image data in this
    # file.
    fine_temp_offset1, fine_temp_offset2, distance, *rest, unit_flag, high_gain_mode_flag = struct.unpack('<9IHHI', header[34:78])
    distance /= 1e4
    
    if fine_temp_offset1 != fine_temp_offset2:
        warnings.warn(f'File lists two different zero offsets for the fine image data {fine_temp_offset1} and {fine_temp_offset2}. Resulting radiometric data might be offset. Please report this with an example file to code@jaseg.de.')

    if print_debug_information:
        print('[infiray_irg debug] Matched model:', model)
        import textwrap
        print(textwrap.dedent(f'''
            [infiray_irg debug] {header_len=}, {coarse_section_length=}, {y_res=}, {x_res=},
            [infiray_irg debug] {flag0=}, {_unk1=}, {_zero1=}, {fine_offset=}, {_unk2=}, {jpeg_length=},
            [infiray_irg debug] {y_res_2=}, {x_res_2=}, {emissivity=} {distance=}
            [infiray_irg debug] {fine_temp_offset1=} {fine_temp_offset1=} {rest=}, {high_gain_mode_flag=} {unit_flag=}'''))

    if x_res*y_res != coarse_section_length:
        raise ValueError('Resolution mismatch in header')
        
    vis_jpg = None
    coarse_img = np.frombuffer(consume(coarse_section_length), dtype=np.uint8).reshape((y_res, x_res))
    fine_img = np.frombuffer(consume(x_res*y_res*2), dtype=np.uint16).reshape((y_res, x_res))

    if model == 'c201':
        if header[-2:] != bytes([0xac,0xca]):
            raise ValueError(f'Header end marker not found. Got header: {header[-2]:02x} {header[-1]:02x}')

        if flag0 == 1: # Seen in Autel Robotics Evo II Dual 640T V3 file.
            # I now have two files from different drones of this manufacturer.
            fine_img = (fine_img / 10) - 273.15

        else: # C201 files
            # 1/16th Kelvin steps
            fine_img = (fine_img / 16) - 273.15

            # The offset for low gain mode images is a bit unclear. It seems all readings around room temperature and
            # below in low gain mode are kind of garbage.

        if jpeg_length > 0:
            # I have seen a file from an Autel Robotics Evo II Dual 640T V3 that looks like a C201 file, but lacks the
            # visible data.
            vis_jpg = Image.open(io.BytesIO(consume(jpeg_length)))

    elif model == 'other':
        if header[-2:] != bytes([0xac,0xca]):
            raise ValueError(f'Header end marker not found. Got header: {header[-2]:02x} {header[-1]:02x}')
        # 0.1 Kelvin steps
        fine_img = fine_img / 10 - 273.15

        vis_jpg = Image.open(io.BytesIO(data))

    else:
        fine_img = fine_img / 10 - 273.2

        # In my example file, data now contains the JSON '{"roi":[]}' and no JPG. We ignore that.
    
    return coarse_img, fine_img, vis_jpg

