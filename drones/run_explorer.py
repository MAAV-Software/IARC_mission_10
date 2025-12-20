"""Example TCP socket client."""
import os
import cv2
import pathlib
import socket
from ultralytics import YOLOWorld
from roles.explorer import ExploreDrone

# for now, simulate the "picture" taking using the training blender images
def map_0(img_dir, coords_list):

    camera_locs = [
        (0, 6.0338),
        (0, 5.0338),
        (0, 4.0338),
        (0, 3.0338),
        (0, 2.0338),
        (-0.5, 2.0338),
        (-0.5, 3.0338),
        (-0.5, 4.0338),
        (-0.5, 5.0338),
        (-0.5, 6.0338),
        (-1, 6.0338),
        (-1, 5.0338),
        (-1, 4.0338),
        (-1, 3.0338),
        (-1, 2.0338),
        (-1.5, 2.0338),
        (-1.5, 3.0338),
        (-1.5, 4.0338),
        (-1.5, 5.0338),
        (-1.5, 6.0338),
        (-2, 6.0338),
        (-2, 5.0338),
        (-2, 4.0338),
        (-2, 3.0338),
        (-2, 2.0338),
        (-2.5, 2.0338),
        (-2.5, 3.0338),
        (-2.5, 4.0338),
        (-2.5, 5.0338),
        (-2.5, 6.0338),
        (-3, 6.0338)
    ] # This is hard-coded from my blender environment, should be taken from the GPS coordinates tho
    all_results = {}

    with os.scandir(img_dir) as entries:
        for i, entry in enumerate(entries):
            # Function to loop through and print out the classes, confidence and bounding box coordinates
            def print_output(all_locations, key, img_width, img_height):
                bounding_boxes = all_locations[key]
                for box in bounding_boxes:
                    # Get the coordinates for each box
                    x_min, y_min, x_max, y_max = box.xyxy[0].tolist()

                    cls = int(box.cls[0].item())  # Class index
                    class_name = model.names[cls] # Class name
                    coords_list.append((class_name, key[0], key[1], x_min / img_width, y_min / img_height, x_max / img_width, y_max / img_height))

            # Run the predictions
            camera_loc = camera_locs[i]
            current_dir = pathlib.Path(__file__).parent
            model_path = current_dir / "weights" / "yolo-weights.pt" 
            model = YOLOWorld(model_path)
            image_path = f"{img_dir}/{entry.name}" # Output from the camera script
            image = cv2.imread(image_path)
            img_height, img_width, _ = image.shape
            results = model.predict(image,conf=0.4, verbose=False)
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
    map_0(img_dir, coords_list)
    ExploreDrone(hostname, 8001, hostname, 8000, coords_list) # For now, just simulating on one laptop, so same hostname for both manager and explorer


if __name__ == "__main__":
    main()