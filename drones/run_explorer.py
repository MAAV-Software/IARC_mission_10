"""Example TCP socket client."""
import os
import cv2
import pathlib
from ultralytics import YOLOWorld
from roles.explorer import ExploreDrone

# for now, simulate the "picture" taking using the training blender images
def map_0(img_dir, coords_list):

    with os.scandir(img_dir) as entries:
        for entry in entries:
            # Function to loop through and print out the classes, confidence and bounding box coordinates
            def print_output(bounding_boxes, img_width, img_height):
                for box in bounding_boxes:
                    # Get the coordinates for each box
                    x_min, y_min, x_max, y_max = box.xyxy[0].tolist()

                    conf = box.conf[0].item()  # Confidence score
                    cls = int(box.cls[0].item())  # Class index
                    class_name = model.names[cls] # Class name
                    loc_placeholder = "loc_placeholder"

                    coords_list.append((loc_placeholder, x_min / img_width, y_min / img_height, x_max / img_width, y_max / img_height))

            # Run the predictions
            current_dir = pathlib.Path.cwd()
            model_path = current_dir / "weights" / "yolo-weights" 
            model = YOLOWorld(model_path)
            image_path = f"{img_dir}/{entry.name}" # Output from the camera script
            image = cv2.imread(image_path)
            img_height, img_width, _ = image.shape
            results = model.predict(image,conf=0.4, verbose=False)
            bounding_boxes = results[0].boxes
            print_output(bounding_boxes, img_width, img_height)

def main():

    # dir for images (Using blender training images for now), will need to update with real drone images later
    current_dir = pathlib.Path.cwd()
    img_dir = current_dir.parent / "images"
    coords_list = []
    map_0(img_dir, coords_list)
    ExploreDrone("rpi2", 8000, coords_list)


if __name__ == "__main__":
    main()