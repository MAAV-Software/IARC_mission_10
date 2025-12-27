import sys
import numpy as np
import pathlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def plot_zones(grid, radius_w, radius_h, center):
    """
    Create a function that plots out a 1 ft square zone around each mine
    
    :param grid: the grid that we have plot all of our zones on
    :param radius_w: the radius in the width or x dimension for 1 ft
    :param radius_h: the radius in the height or y dimension for 1 ft
    :param center: the center of the 
    """
    center_x, center_y = center
    map_height, map_width = grid.shape
    grid[center_y, center_x] = 1 # numpy arrays go rows by columns, so it would actually be like (y, x)
    for i in range(radius_w):
        for j in range(radius_h):
            if (center_y - j >= 0) and (center_x - i >= 0):
                grid[center_y - j, center_x - i] = 1

    for i in range(radius_w):
        for j in range(radius_h):
            if (center_y + j < map_height) and (center_x + i < map_width):
                grid[center_y + j, center_x + i] = 1
    
    for i in range(radius_w):
        for j in range(radius_h):
            if (center_y - j >= 0) and (center_x + i < map_width):
                grid[center_y - j, center_x + i] = 1
    
    for i in range(radius_w):
        for j in range(radius_h):
            if (center_y + j < map_height) and (center_x - i >= 0):
                grid[center_y + j, center_x - i] = 1


world_bounds = []
curr_dir = pathlib.Path(__file__).parent
world_bounds_path = curr_dir / "world_bounds.txt"
output_path = curr_dir.parent / "output" / "grid-output.txt"
with open(world_bounds_path, "r") as f:
    for line in f:
        values = line.strip().split()
        world_bounds.append((round(float(values[0]), 2), round(float(values[1]), 2)))

x_bias = world_bounds[0][0]
y_bias = world_bounds[0][1]
for i, bound in enumerate(world_bounds):
    x_bound, y_bound = bound
    world_bounds[i] = (x_bound - x_bias, y_bound - y_bias)

for line in sys.stdin:
    scale = line.strip().split()
    scale = int(scale[0]) # This value is how much we are rounding by for precision
    break

map_width = int((world_bounds[3][0] - world_bounds[0][0]) * (10**scale))
map_height = int((world_bounds[3][1] - world_bounds[0][1]) * (10**scale))
grid = np.zeros((map_height, map_width))

world_width = 14.93
world_height = 20.24

# These represent the amount of distance 1 px represents in ft
dw = world_width / map_width
dh = world_height / map_height

# Represent the number of pixels for the 1 ft border around each mine
zone_radius_width = int(1 / dw)
zone_radius_height = int(1 / dh)
# print(zone_radius_width, zone_radius_height)
# print(map_width, map_height)

for line in sys.stdin:
    values = line.strip().split()
    if len(values) == 1:
        continue
    
    obj, loc_x, loc_y = values
    if not obj == "mine":
        continue
    
    # Bias the coordinates, similar to float point representation in 370
    local_x = float(loc_x) - x_bias
    local_y = float(loc_y) - y_bias

    if local_x >= world_bounds[3][0] or local_y >= world_bounds[3][1]: # Those values represent the max bounds
        # print(f"Out of bounds max {local_x} {local_y} coming from {loc_x} {loc_y}")
        continue

    if local_x < 0 or local_y < 0:
        continue
    
    grid_x_idx = int(local_x * (10**scale))
    grid_y_idx = int(local_y * (10**scale))
    plot_zones(grid, zone_radius_width, zone_radius_height, (grid_x_idx, grid_y_idx))
grid = grid.astype(int)

with open(output_path, "w") as f:
    pass

with open(output_path, "a") as f:
    for row in grid:
        # Convert each element to string and join with spaces (or commas)
        f.write(" ".join(map(str, row)) + "\n")

cmap = ListedColormap(["blue", "red"])

plt.imshow(grid, cmap=cmap)
plt.colorbar(ticks=[0, 1])
plt.title("0 = Blue, 1 = Red")
plt.savefig("mine_detections.png", dpi=300) 
plt.show()


