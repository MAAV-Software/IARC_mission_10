"""Example TCP socket client."""
import os
import cv2
import pathlib
import socket
from ultralytics import YOLOWorld
from roles.explorer import ExploreDrone

# for now, simulate the "picture" taking using the training blender images so this will be empty for now
# for future, need a function that takes pictures, uploades to img_dir and then also notes down the location using coordinates
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
        (-1.5, 2.0338, 2),
        (-1.5, 3.0338, 2),
        (-1.5, 4.0338, 2),
        (-1.5, 5.0338, 2),
        (-1.5, 6.0338, 2),
        (-2, 6.0338, 2),
        (-2, 5.0338, 2),
        (-2, 4.0338, 2),
        (-2, 3.0338, 2),
        (-2, 2.0338, 2),
        (-2.5, 2.0338, 2),
        (-2.5, 3.0338, 2),
        (-2.5, 4.0338, 2),
        (-2.5, 5.0338, 2),
        (-2.5, 6.0338, 2),
        (-3, 6.0338, 2)
    ] # This is hard-coded from my blender environment, should be taken from the GPS coordinates tho

    picture_paths = []
    with os.scandir(img_dir) as entries:
        for entry in sorted(entries, key=lambda e: e.stat().st_mtime): # Make sure that the files are sorted by name since we want to preserve order
            image_path = img_dir / entry.name
            print(image_path)
            picture_paths.append(image_path)

    for i in range(len(camera_locs)):
        picture_and_locs.append((camera_locs[i], picture_paths[i]))
    
    return picture_and_locs

def map_0(drone_output, coords_list):

    all_results = {}

    for i, entry in enumerate(drone_output):
        # Function to loop through and print out the classes, confidence and bounding box coordinates
        def print_output(all_locations, key, img_width, img_height):
            bounding_boxes = all_locations[key]
            for box in bounding_boxes:
                # Get the coordinates for each box
                x_min, y_min, x_max, y_max = box.xyxy[0].tolist()

                cls = int(box.cls[0].item())  # Class index
                class_name = model.names[cls] # Class name
                coords_list.append((class_name, key[0], key[1], key[2], x_min / img_width, y_min / img_height, x_max / img_width, y_max / img_height))

        # Run the predictions
        camera_loc, image_path = drone_output[i] # Output from the camera script
        current_dir = pathlib.Path(__file__).parent
        model_path = current_dir / "weights" / "12-2-25.pt" 
        model = YOLOWorld(model_path)
        image = cv2.imread(image_path)
        img_height, img_width, _ = image.shape
        results = model.predict(image,conf=0.4, verbose=False)
        # results[0].show()
        bounding_boxes = results[0].boxes
        all_results[camera_loc] = bounding_boxes
        print_output(all_results, camera_loc, img_width, img_height)

def main():

    hostname = socket.gethostname()
    print(hostname)
    # dir for images (Using blender training images for now), will need to update with real drone images later
    current_dir = pathlib.Path(__file__).parent
    img_dir = current_dir.parent / "images"
    coords_list = []
    drone_output = take_picture(img_dir)
    map_0(drone_output, coords_list)
    ExploreDrone(hostname, 8001, hostname, 8000, coords_list) # For now, just simulating on one laptop, so same hostname for both manager and explorer


if __name__ == "__main__":
    main()