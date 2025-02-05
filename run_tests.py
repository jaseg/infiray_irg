from pathlib import Path

import infiray_irg

test_files = sorted(Path('test_pictures').glob('*.irg'))

for f in test_files:
    try:
        coarse, fine, vis = infiray_irg.load(f.read_bytes(), print_debug_information=True)
        print('\033[93m', f'{f.name:>20}', 'Coldest pixel:', fine.min(), 'C', 'Hottest pixel:', fine.max(), 'C', '\033[0m')
    except Exception as e:
        print(f'Error parsing {f}')
        raise e

print()
print('Header diffs:')

for offset, legend in {
         0: 'magc hlen coars_len yres xres flg0 unk1 zero fine unk2 jpeg_len_ yres xres emissivit fine_off1 fine_off2 distance_',
        64: '                    unit gain'}.items():
    print(f'{" ":>20}', legend)
    test_headers = {f: f.read_bytes()[offset:offset+64] for f in test_files}
    header_idx_diffs = [len(set(header[i] for header in test_headers.values())) > 1 for i in range(64)]
    for f, header in test_headers.items():
        print(f'{str(f.name):>20}', ' '.join(
            ''.join(
                (f'\033[91m{header[i]:02x}' if header_idx_diffs[i] else f'\033[0m{header[i]:02x}')
                for i in range(chunk, chunk+2))
                    for chunk in range(0, 64, 2)
            )+'\033[0m')
