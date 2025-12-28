import sys
import numpy as np
import pathlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

grid = []
for line in sys.stdin:
    values = list(map(int, line.strip().split()))
    grid.append(values)


grid = np.array(grid)

cmap = ListedColormap(["white", "red", "green"])
plt.figure(figsize=(10, 10))
plt.imshow(grid, cmap=cmap)
plt.colorbar(ticks=[0, 1, 2])
plt.title("0 = white, 1 = Red, 2=Green")
plt.gca().invert_yaxis()
plt.savefig("output_path.png", dpi=300) 
plt.show()

