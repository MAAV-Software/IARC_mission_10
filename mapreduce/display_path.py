import sys
import numpy as np
import pathlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

grid = []
path_width = 0
path_height = 0
for line in sys.stdin:
    values = line.strip().split()
    if len(values) == 2:
        path_width = values[0]
        path_height = values[1]
        continue
    
    values = list(map(int, values))
    grid.append(values)


grid = np.array(grid)

cmap = ListedColormap(["white", "red", "green"])
plt.figure(figsize=(10, 10))
plt.imshow(grid, cmap=cmap)
plt.colorbar(ticks=[0, 1, 2])
plt.title(f"Mine = Red, Path = Green, Path_width = {path_width}, Path Height = {path_height}")
plt.gca().invert_yaxis()
plt.savefig("output_path.png", dpi=300) 
plt.show()

