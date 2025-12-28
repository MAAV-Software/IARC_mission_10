import sys
import math
import pathlib

current_dir = pathlib.Path(__file__).parent.parent
map_output = current_dir / "output" / "map-2-output.txt"
with open(map_output, "w") as f: # Clear contents before writing into it
    pass

# These are global specs about our camera that are static
v_fov = math.radians(51)
h_fov = math.radians(65)
scale = 2 # How much to round by

with open(map_output, "a") as f:
    f.write(f"{scale}\n")

for line in sys.stdin:
    key, values = line.strip().split("\t") # Key represents the classification, and values represents the location data for the camera and the detection
    classification = key
    x_loc, y_loc, alt, norm_x_min, norm_y_min, norm_x_max, norm_y_max = values.split(",")
    # first three values represent the camera's position (x, y, altitude)
    # last 4 values represent the location of the detected object within the image

    # Get the normalized center of the detected object
    norm_x = (float(norm_x_min) + float(norm_x_max)) / 2
    norm_y = (float(norm_y_min) + float(norm_y_max)) / 2

    # Get the dimension of the camera frame
    hor_rad = h_fov / 2
    view_x = 2 * float(alt) * math.tan(hor_rad)
    
    vert_rad = v_fov / 2
    view_y = 2 * float(alt) * math.tan(vert_rad)

    # Get the midway distance for the image
    mid_x = view_x / 2
    mid_y = view_y / 2

    # These values represent how far the detect object is truly shifted in the camera's view
    delt_x = norm_x * view_x
    delt_y = norm_y * view_y

    # Calculate the origin point
    origin_x = float(x_loc) - float(mid_x)
    origin_y = float(y_loc) + float(mid_y)

    # Now add the offset to the origin to get the global coordinate (this is still simulated using blender but the workflow should be the same but with GPS)
    global_x = round(origin_x + delt_x, scale)
    global_y = round(origin_y - delt_y, scale)
    
    with open(map_output, "a") as f:
        f.write(f"{key} {global_x} {global_y}\n")



