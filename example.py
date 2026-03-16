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

if vis:
    ax3.imshow(vis)
    ax3.set_title('Visual')

ax4.hist(fine.flatten(), bins=100)
ax4.set_title('Temperature histogram')
ax4.set_xlabel('degrees Celsius')

fig.tight_layout()
fig.savefig('plot.png')

print('Coldest pixel:', fine.min(), 'C', 'Hottest pixel:', fine.max(), 'C')
