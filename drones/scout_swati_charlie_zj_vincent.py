
import os
import cv2
import pathlib
from ultralytics import YOLOWorld
import math

# for now, simulate the "picture" taking using the training blender images so this will be empty for now
# for future, need a function that takes ictures, uploades to img_dir and then also notes down the location using coordinates
def take_picture(img_dir):
    picture_and_locs = []

    camera_locs = [
        (0, 6.0338, 2),
        (0, 5.0338, 2),
        (0, 4.0338, 2),
        (0, 3.0338, 2),
        (0, 2.0338, 2),
        (-0.5, 2.0338, 2),
        (-0.5, 3.0338, 2),
        (-0.5, 4.0338, 2),
        (-0.5, 5.0338, 2),
        (-0.5, 6.0338, 2),
        (-1, 6.0338, 2),
        (-1, 5.0338, 2),
        (-1, 4.0338, 2),
        (-1, 3.0338, 2),
        (-1, 2.0338, 2),
    ] # This is hard-coded from my blender environment, should be taken from the GPS coordinates tho

    picture_paths = []
    with os.scandir(img_dir) as entries:
        for entry in sorted(entries, key=lambda e: e.stat().st_mtime): # Make sure that the files are sorted by name since we want to preserve order
            image_path = img_dir / entry.name
            if entry.name != ".DS_Store":
                picture_paths.append(image_path)

    for i in range(len(camera_locs)):
        picture_and_locs.append((camera_locs[i], picture_paths[i]))
    
    return picture_and_locs

def map_0(drone_output, coords_list):

    all_results = {}

    for i, entry in enumerate(drone_output):
        # Function to loop through and print out the classes, confidence and bounding box coordinates
        def print_output(all_locations, key, img_width, img_height):
            bounding_boxes = all_locations[key] # key represents the global location of the mine in (x, y, z)
            for box in bounding_boxes:
                # Get the coordinates for each box
                x_min, y_min, x_max, y_max = box.xyxy[0].tolist() # still will need to normalizez it so that we can get the "global coords"

                cls = int(box.cls[0].item())  # Class index
                class_name = model.names[cls] # Class name
                coords_list.append((class_name, key[0], key[1], key[2], x_min / img_width, y_min / img_height, x_max / img_width, y_max / img_height))

        # Run the predictions
        camera_loc, image_path = drone_output[i] # Output from the camera script
        parent_dir = pathlib.Path(__file__).parent.parent
        model_path = parent_dir / "weights" / "blender-weights.pt" 
        model = YOLOWorld(model_path)
        image = cv2.imread(image_path)
        img_height, img_width, _ = image.shape
        results = model.predict(image,conf=0.4, verbose=False)
        bounding_boxes = results[0].boxes
        all_results[camera_loc] = bounding_boxes
        print_output(all_results, camera_loc, img_width, img_height)

def main():
    # dir for images (Using blender training images for now), will need to update with real drone images later
    # Use this when we are actually taking pictures from the drone, upload the images taken from the drone to this path
    parent_dir = pathlib.Path(__file__).parent
    img_dir = parent_dir.parent / "taken_images_vzsc" # Use a folder called training_images for now, but will need to adapt this parameter for drone pics later

    coords_list = [] # Stores all the information about the mines that we need
    drone_output = take_picture(img_dir)
    map_0(drone_output, coords_list)
    # print(coords_list) # Can see all of the locations of all the mines

    # TODO We now have the "global" location of the mines, as well as the bounding boxes of the mines
    # What we need to do now is to make it so that we calculate the location of the mine in the global space
    # We can now just assume that the center of the bounding box is the center of the mine

    with open("DervinSmellsLikePoop.csv", "w") as f:    
        f.write("x,y\n")
        for (c, x, y, z, pic_x_min, pic_y_min, pic_x_max, pic_y_max) in coords_list:
         
            loc_pic_vertical = 2 * z * math.tan(math.radians(25.5))
            loc_pic_horizontal = 2 * z * math.tan(math.radians(32.5))

            mine_x = (pic_x_min + pic_x_max) / 2
            mine_y = (pic_y_min + pic_y_max) / 2

            # Relative mine coordinates with 0.5,0.5 center
            mine_x_relation = mine_x - .5
            mine_y_relation = mine_y - .5

            scaled_x = mine_x_relation * loc_pic_horizontal
            scaled_y = mine_y_relation * loc_pic_vertical

            global_x = scaled_x + x
            global_y = y - scaled_y

            f.write(f"{global_x},{global_y}\n")
    
    
if __name__ == "__main__":
    main()
