# Infiray IRG file format parser

This python module contains a simple parser for the "IRG" file format that the Infiray C200 series thermal cameras use
to dump their raw data. The files contain three things: A thermal image with 8 bit resolution with contrast scaled to
fit the 0...255 range, a thermal image with 16 bit resolution containing absolute temperature values with 1/16 K
resolution, and a JPEG with the image from the low-res visual camera.

## Requirements

pillow and numpy

## API

Call `infiray_irg.load(data)` with a `bytes` object containing the IRG file's contents. It will return a tuple `(coarse,
fine, vis)` of the coarse and fine images as numpy arrays, followed by the visual image as a pillow image. The coarse
image has dtype uint8 and contains values from 0 to 255, where 0 is the coldest pixel in the image, and 255 is the
hottest. The fine image has dtype float and contains absolute degree Celsius values.

## Example

```python
from matplotlib import pyplot as plt
from pathlib import Path

import infiray_irg

coarse, fine, vis = infiray_irg.load(Path('example.irg').read_bytes())

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 18))

ax1.imshow(coarse)
ax1.set_title('Coarse contrast-maximized')

fine_plt = ax2.imshow(fine)
ax2.set_title('Fine absolute temperatures')
fig.colorbar(fine_plt, ax=ax2, location='right', label='degrees Celsius')

ax3.imshow(vis)
ax3.set_title('Visual')

ax4.hist(fine.flatten(), bins=100)
ax4.set_title('Temperature histogram')
ax4.set_xlabel('degrees Celsius')

fig.tight_layout()
fig.savefig('plot.png')

print('Coldest pixel:', fine.min(), 'C', 'Hottest pixel:', fine.max(), 'C')
```

## Bugs

If you find a bug, or find a file that this library can't load, please send me an email at <code@jaseg.de>.

## License

This module is licensed under the MIT license.

