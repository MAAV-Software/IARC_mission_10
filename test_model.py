from ultralytics import YOLOWorld
from PIL import Image
import cv2
import numpy as np
import time
    
# Function to loop through and print out the classes, confidence and bounding box coordinates
def print_output(bounding_boxes, img_width, img_height):
    for box in bounding_boxes:
        # Get the coordinates for each box
        x_min, y_min, x_max, y_max = box.xyxy[0].tolist()

        conf = box.conf[0].item()  # Confidence score
        cls = int(box.cls[0].item())  # Class index
        class_name = model.names[cls] # Class name

        # Print out the class name, confidence score as well as the bouding box coordinates
        print(" ")
        print("Class:", class_name)
        print("Confidence:", conf)
        print("norm x min: ", x_min / img_width, " ", "norm y_min: ", y_min / img_height, " ", "norm x_max: ", x_max / img_width, " ", "norm y_max: ", y_max / img_height, " ")
init_time = time.time()
# Load the YOLO world model
model_path = "./weights/blender-weights.pt"
model = YOLOWorld(model_path)
end_time = time.time()
print(f"Elapsed Time: {end_time - init_time}")

image_path = "./test_images/IMG_5893pfm1-mine.jpeg" # Output from the camera script

# Read in the image and open it
image = cv2.imread(image_path)
original_image = Image.open(image_path)

img_height, img_width, channels = image.shape
print(img_width, img_height)

# Predict using the YOLO model and show the result
results = model.predict(image,conf=0.3)
results[0].show()

# Get the bounding boxes
bounding_boxes = results[0].boxes  # Bounding boxes for the YOLO Predictions Image
print_output(bounding_boxes, img_width, img_height) # Loop through the bounding boxes and print out their coordinates
