"""Plot the Oster curve — optimal binaural beat per carrier frequency.

Usage: python plot_oster.py
Saves: docs/oster-curve.png
"""

import matplotlib.pyplot as plt
import numpy as np

# Oster curve data: carrier (Hz) -> max detectable beat (Hz)
DATA = [
    (10, 0.235), (20, 0.444), (30, 0.615), (40, 0.768), (50, 0.964),
    (60, 1.21), (70, 1.451), (80, 1.659), (90, 1.856), (100, 2.054),
    (110, 2.265), (120, 2.581), (130, 2.903), (140, 3.266), (150, 3.669),
    (160, 4.073), (170, 4.596), (180, 5.104), (190, 5.835), (200, 6.821),
    (210, 7.66), (220, 8.599), (230, 9.551), (240, 10.604), (250, 12.037),
    (260, 13.935), (270, 15.396), (280, 17.023), (290, 18.571), (300, 19.453),
    (310, 20.815), (320, 21.767), (330, 22.41), (340, 23.248), (350, 23.843),
    (360, 24.459), (370, 24.813), (380, 25.14), (390, 25.604), (400, 25.771),
    (410, 26.026), (420, 26.103), (430, 26.185), (440, 26.232), (450, 26.249),
    (460, 26.25), (470, 26.108), (480, 25.775), (490, 25.566), (500, 25.41),
    (510, 25.083), (520, 24.688), (530, 24.257), (540, 23.836), (550, 23.393),
    (560, 22.993), (570, 22.387), (580, 21.466), (590, 20.535), (600, 19.513),
    (610, 18.116), (620, 17.206), (630, 16.295), (640, 15.479), (650, 14.836),
    (660, 14.087), (670, 13.155), (680, 12.58), (690, 11.896), (700, 11.21),
    (710, 10.61), (720, 10.029), (730, 9.492), (740, 8.722), (750, 8.364),
    (760, 8.059), (770, 7.703), (780, 7.318), (790, 7.002), (800, 6.661),
    (810, 6.356), (820, 6.116), (830, 5.881), (840, 5.642), (850, 5.44),
    (860, 5.28), (870, 5.138), (880, 4.846), (890, 4.703), (900, 4.565),
    (910, 4.396), (920, 4.203), (930, 4.053), (940, 3.894), (950, 3.744),
    (960, 3.623), (970, 3.514), (980, 3.391), (990, 3.274), (1000, 3.161),
    (1010, 3.015), (1020, 2.855), (1030, 2.697), (1040, 2.576), (1050, 2.46),
    (1060, 2.347), (1070, 2.236), (1080, 2.124), (1090, 2.011), (1100, 1.896),
    (1110, 1.775), (1120, 1.644), (1130, 1.523), (1140, 1.428), (1150, 1.354),
    (1160, 1.283), (1170, 1.199), (1180, 1.109), (1190, 1.021), (1200, 0.974),
    (1210, 0.968), (1220, 0.924), (1230, 0.85), (1240, 0.762), (1250, 0.666),
    (1260, 0.575), (1270, 0.555), (1280, 0.562), (1290, 0.536), (1300, 0.498),
    (1310, 0.453), (1320, 0.406), (1330, 0.372), (1340, 0.37),
]

carriers = np.array([d[0] for d in DATA])
beats = np.array([d[1] for d in DATA])

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(carriers, beats, color="tab:blue", linewidth=2)
ax.fill_between(carriers, beats, alpha=0.1, color="tab:blue")

# Brainwave band regions on the y-axis
y_limit = 28
bands = [
    ("Delta", 0.5, 4, "#4a90d9"),
    ("Theta", 4, 8, "#50c878"),
    ("Alpha", 8, 13, "#f5a623"),
    ("Beta", 13, 30, "#e67e22"),
    ("Gamma", 30, y_limit, "#e74c3c"),
]
for label, y0, y1, color in bands:
    y_top = min(y1, y_limit)
    if y_top > y0:
        ax.axhspan(y0, y_top, alpha=0.07, color=color, zorder=0)
        ax.text(1345, (y0 + y_top) / 2, label, fontsize=8, color=color,
                va="center", ha="right", fontweight="bold")

# Annotate our default carriers
defaults = [(200, "Low carrier\n(200 Hz)", 40, 2), (400, "High carrier\n(400 Hz)", -120, -3)]
for x, label, dx, dy in defaults:
    y = np.interp(x, carriers, beats)
    ax.axvline(x, ymax=y / y_limit, linestyle="--", color="gray", linewidth=0.8)
    ax.plot(x, y, "o", color="tab:red", markersize=6)
    ax.annotate(
        label, xy=(x, y), xytext=(x + dx, y + dy),
        arrowprops=dict(arrowstyle="->", color="gray", linewidth=0.8),
        fontsize=9, color="tab:red", fontweight="bold",
    )

ax.set_xlabel("Carrier frequency (Hz)", fontsize=11)
ax.set_ylabel("Optimal beat frequency (Hz)", fontsize=11)
ax.set_title("Oster curve — Binaural beat perception vs carrier frequency", fontsize=13)
ax.set_xlim(0, 1350)
ax.set_ylim(0, y_limit)
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig("docs/oster-curve.png", dpi=150)
print("Saved docs/oster-curve.png")
