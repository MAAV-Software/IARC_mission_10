import bpy
import bpy_extras
import random
import os
import shutil
import math
from mathutils import Matrix
import time

# Define helper functions

def convert_speed(speed):
    # We want to convert the speed into the distance to move per frame
    return speed * time_interval

# Create a function to create a defined path (right now we are mowing the lawn)
def create_path(speed, starting_location, x_bounds, y_bounds):
    path = []
    pos_x, pos_y = starting_location
    min_x, max_x = x_bounds
    min_y, max_y = y_bounds
    
    # Will create the lawn mowing effect going from bottom right to bottom left
    while pos_x >= min_x:
        print(f"The pos_y is {pos_y} and the max_y is {max_y}")
        while pos_y >= min_y and pos_y <= max_y:
            if pos_y - speed >= min_y and pos_y - speed <= max_y:
                pos_y -= speed
                path.append(("y", -1 * speed))
            else:
                break
        pos_x -= 0.5
        path.append(("x", -0.5))
        speed *= -1
    
    return path


# Get all of the objects within the camera's frame
def find_objects_in_scene(position, height, mines):
    # Goal is to find the objects within the camera's view since we know the object's location and can find the bounding boxes of the camera
    pos_x, pos_y = position
    in_frame = []
    
    # Get the dimension of the camera frame
    hor_rad = math.radians(32.5)
    view_y = 2 * height * math.tan(hor_rad)
    
    vert_rad = math.radians(25.5)
    view_x = 2 * height * math.tan(vert_rad)
    
    delt_x = view_x / 2
    delt_y = view_y / 2
    
    min_x = pos_x - delt_x
    max_x = pos_x + delt_x
    
    min_y = pos_y - delt_y
    max_y = pos_y + delt_y
    
    for key in mines:
        location = mines[key]
        mine_x, mine_y, _ = location
        if not (mine_x > min_x and mine_x < max_x):
            continue
        if not (mine_y > min_y and mine_y < max_y):
            continue
        in_frame.append(key)
    
    return in_frame

# Create a function to get the info needed for the label x_center, y_center, width, height
def get_labels(camera, mine):
    scene = bpy.context.scene
    height = camera.location.z
    class_id = 0
    
    # Get the dimension of the camera view frame
    hor_rad = math.radians(32.5)
    view_y = 2 * height * math.tan(hor_rad)
    
    vert_rad = math.radians(25.5)
    view_x = 2 * height * math.tan(vert_rad)
    
    local_origin_x = camera.location.x - (view_x / 2)
    local_origin_y = camera.location.y - (view_y / 2)
    
    mine_local_x = mine.location.x - local_origin_x
    mine_local_y = mine.location.y - local_origin_y
    
    norm_x_center = mine_local_x / view_x # These are blender's x axis and not YOLO's x axis
    norm_y_center = mine_local_y / view_y # These are blender's y axis and not YOLO's y axis
    
    mine_x_length = 0.12
    mine_y_length = 0.061
    mine_rotation = mine.rotation_euler.z
    
    bounding_box_x_length, bounding_box_y_length = get_bounding_box_dimensions(mine_rotation, mine_x_length, mine_y_length)
    x_norm = bounding_box_x_length / view_x # These are blender's x axis and not YOLO's x axis
    y_norm = bounding_box_y_length / view_y # These are blender's y axis and not YOLO's y axis
    
    label = [class_id, norm_y_center, norm_x_center, y_norm, x_norm]
    return label
    
    
# Create a function to get the dimensions of the bounding boxes (unnormalized) given the object's location and rotation
def get_bounding_box_dimensions(angle, mine_x, mine_y):
    x_length = None
    y_length = None
    if angle >= 0 and angle <= (math.pi / 2):
        x = mine_x
        y = mine_y
        x_length = (x * math.cos(angle)) + (y * math.sin(angle))
        y_length = (x * math.sin(angle)) + (y * math.cos(angle))
    elif angle > (math.pi / 2) and angle <= math.pi:
        new_angle = angle - (math.pi / 2)
        x = mine_y
        y = mine_x
        x_length = (x * math.cos(new_angle)) + (y * math.sin(new_angle))
        y_length = (x * math.sin(new_angle)) + (y * math.cos(new_angle))
    elif angle > math.pi and angle <= (3 * math.pi / 2):
        new_angle = angle - math.pi
        x = mine_x
        y = mine_y
        x_length = (x * math.cos(new_angle)) + (y * math.sin(new_angle))
        y_length = (x * math.sin(new_angle)) + (y * math.cos(new_angle))
    else:
        new_angle = angle - (3 * math.pi / 2)
        x = mine_y
        y = mine_x
        x_length = (x * math.cos(new_angle)) + (y * math.sin(new_angle))
        y_length = (x * math.sin(new_angle)) + (y * math.cos(new_angle))
    return (x_length, y_length)
    

# --------------------------------- #

# Define global variables and get baseline stuff out of the way
start_time = time.time()  # record start time
uniqname = "" # TODO Insert your uniqname here

stl_filepath = "" # TODO change the stl filepath to match yours

num_iterations = 1
scale = 1
num_mines = 10
height = 2
speed = 2 # (m/s)
time_interval = 0.5 # (1 second per picture)

context = bpy.context
IARC_hex = "#97CBC2FF"
mat = bpy.data.materials.new("mine_green")
mat.use_nodes = True
principled = mat.node_tree.nodes['Principled BSDF']
principled.inputs['Base Color'].default_value = (0.309, 0.597, 0.539, 1)

# This is to do some directory management

overwrite = True # Boolean determining if we want to overwrite old previous images

img_dir = "" # TODO specify an output image directory
labels_dir = "" # TODO specifyt an output labels direcotry
num_files = 0

if overwrite:
    if os.path.exists(img_dir):
        shutil.rmtree(img_dir)
        os.mkdir(img_dir)
        print(f"Directory '{img_dir}' exist and cleard its contents!")
    else:
        os.mkdir(img_dir)
        print(f"Directory '{img_dir}' did not exist and we created it now.")
else:
    num_files += len(os.listdir(img_dir))

# Clear out all of the prexisting labels so that we can repopulate it with new ones

if os.path.exists(labels_dir):
    shutil.rmtree(labels_dir)
    os.mkdir(labels_dir)
    print(f"Directory '{labels_dir}' exist and cleard its contents!")
else:
    os.mkdir(labels_dir)
    print(f"Directory '{labels_dir}' did not exist and we created it now.")

    
# Initialize the bounds of where we want our camera to fly
    
world_coordinate_top_left = (-2.8949, 1.9123)
world_coordinate_top_right = (-2.8949, 6.1338)
world_coordinate_bottom_left = (0, 1.9123)
world_coordinate_bottom_right = (0, 6.1338)

x1, y1 = world_coordinate_top_left
x2, y2 = world_coordinate_top_right
x3, y3 = world_coordinate_bottom_left
x4, y4 = world_coordinate_bottom_right

x_min = min([x1, x2, x3, x4])
x_max = max([x1, x2, x3, x4])

y_min = min([y1, y2, y3, y4])
y_max = max([y1, y2, y3, y4])

# This is now to place down the mines randomly and store their locations (bounding box labels)
    
mine_locations = {}

for i in range(num_iterations):
    print(f"speed is: {speed}")
    name_to_delete = "IARC_PFM-1_mine"
    scene_name = "St.Augustine-grass.037"
    grass = None
    for obj in list(bpy.data.objects):
        if obj.name.startswith(name_to_delete):
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.name.startswith(scene_name):
            grass = obj
        
    for obj in bpy.context.scene.objects:
        obj.animation_data_clear()

    cam = bpy.context.scene.camera
    cam.location.x, cam.location.y = world_coordinate_bottom_right
    cam.location.y -= 0.1
    cam.location.z = height
    cam.keyframe_insert(data_path="location", frame=1)          
    frame = 2
            

    for j in range(num_mines):
        remove_foot = True
        bpy.ops.import_mesh.stl(filepath=stl_filepath)
        mine = bpy.context.object
        mesh = mine.data
        mine.dimensions = [0.12 * scale, 0.061 * scale, 0.020 * scale]
        rand_x = random.uniform(x_min, x_max)
        rand_y = random.uniform(y_min, y_max)
        rand_rotation = random.uniform(0, 2 * math.pi)
    
        # Allows the mine to sit flatly on the gradient of the terrain as it is bumpy

        #make the origin the pottom of cube
        mesh.transform(Matrix.Translation((0, 0, 1)))


        bpy.ops.mesh.primitive_circle_add(
                location=(rand_x, rand_y, 0),
                fill_type='TRIFAN')
                
        foot = context.object
        sw = foot.modifiers.new(name="SW", type='SHRINKWRAP') 
        sw.target = grass
        sw.wrap_method = 'PROJECT'
        sw.use_positive_direction = True
        sw.use_negative_direction = True
        sw.use_project_z = True

        ### set the relation to foot
        mine.parent = foot
        mine.parent_type = 'VERTEX_3'
        n = len(foot.data.vertices)
        mine.parent_vertices = range(1, n, n // 3)

        if remove_foot:
            dg = context.evaluated_depsgraph_get()
            mw = mine.evaluated_get(dg).matrix_world.copy()
            bpy.data.objects.remove(foot)
            mine.matrix_world = mw
            context.view_layer.objects.active = grass
            
        mine.location.z += 0.1 
        mine.rotation_euler.z = rand_rotation
        mine_locations[mine.name] = mine.location
        
        bpy.ops.object.mode_set(mode='EDIT')
        mesh.materials.append(mat)
        bpy.ops.object.mode_set(mode='OBJECT')

    # Now that we have all of the mines loaded, we want to simulate the drone flying by moving the camera around

    path = [] # Will contain all the different movements that the camera will be making
    
    converted_speed = convert_speed(speed)

    starting_location = (cam.location.x, cam.location.y)
    x_bounds = (x_min, x_max)
    y_bounds = (y_min, y_max)
    
    path = create_path(converted_speed, starting_location, x_bounds, y_bounds)

    # Move thorugh the path and note down the objects within that frame

    frame_mines = {}
    item_frames = []
    
    # Also need to get labels in case there are mines in frame 1, pre-path
    cam_loc = (cam.location.x, cam.location.y)
    objects = find_objects_in_scene(cam_loc, height, mine_locations)  # Get the names of the objects within the scene
    if len(objects) > 0:
        all_labels = []
        item_frames.append(1)
        for mine in objects: # For all the mines's names within the scene
            for thing in bpy.context.scene.objects: 
                if thing.name == mine: # Get the actual blender objects with the matching names
                    line = get_labels(cam, thing)
                    all_labels.append(line)
                    print(f"Detected {mine} in frame {frame}")
        frame_mines[1] = all_labels
        
    # Go through the path and get the images that we want with their labels as well

    for movement in path:
        direction, move_speed = movement
        if direction == "x":
            cam.location.x += move_speed
            cam.keyframe_insert(data_path="location", frame=frame)
        elif direction == "y":
            cam.location.y += move_speed
            cam.keyframe_insert(data_path="location", frame=frame)
            
        cam_loc = (cam.location.x, cam.location.y)
        objects = find_objects_in_scene(cam_loc, height, mine_locations)  # Get the names of the objects within the scene
        if len(objects) > 0:
            all_labels = []
            item_frames.append(frame)
            for mine in objects: # For all the mines's names within the scene
                for thing in bpy.context.scene.objects: 
                    if thing.name == mine: # Get the actual blender objects with the matching names
                        line = get_labels(cam, thing)
                        all_labels.append(line)
                        print(f"Detected {mine} in frame {frame}")
            frame_mines[frame] = all_labels
        
        frame += 1
    
    
    # What we can do now is render the keyframes as images
    bpy.context.scene.render.engine = "CYCLES"
    
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "METAL"
    bpy.context.scene.cycles.device = "GPU"
    
    bpy.context.scene.cycles.samples = 1
    bpy.context.scene.cycles.use_denoising = False
    
    scene = bpy.context.scene
    
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x = 3280
    scene.render.resolution_y = 2464
    scene.render.resolution_percentage = 100
    
    scene.frame_start = 1
    scene.frame_end = frame - 1
        
    # Now we start to create the labels, we need to go through each frame and create the labels given the objects in that scene
    for k in range(1, frame):
        label_filename = f"{uniqname}_{k}_{i}.txt"
        label_file = labels_dir + label_filename
        
        img_filename = f"{uniqname}_{k}_{i}.png"
        img_file = img_dir + img_filename

#        scene.frame_set(k)
#        scene.render.filepath = img_file
#        bpy.ops.render.render(write_still=True)
        
        # For frames with no mines, just leave that training file empty
        if not k in item_frames:
            with open(label_file, "w"):
                pass
            continue
        
        # For frames with mines, add the labels into it
        with open(label_file, "w") as f:
            for label in frame_mines[k]:
                print(f"{k} line is {label}")
                f.write(f"{label[0]} {label[1]} {label[2]} {label[3]} {label[4]}\n")

    bpy.ops.object.select_all(action='DESELECT')
    cam.select_set(True)

end_time = time.time()  # record end time
print(f"Execution time: {end_time - start_time:.4f} seconds")

    