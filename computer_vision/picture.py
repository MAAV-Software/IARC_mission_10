# import cv2
from picamera2 import Picamera2
import os
# print(cv2.getBuildInformation())

"""
gst_pipeline = (
	"nvarguscamerasrc sensor_id=0"
	"video/x-raw(memory:NVMM), width=3280. height=2464, framerate=30/01 !"
	"nvvidconv !"
	"videoconvert ! "
	"video/x-raw, format=BGR ! appsink"
)
"""
   
# Open a connection to the webcam (0 is the default camera)
# cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
cam = Picamera2()
# cam.take_photo("test1.jpg")

config = cam.create_still_configuration()
cam.configure(config)

cam.start()
sleep(2)

cam.capture_file("image.jpg")

cam.stop()
"""
# Check if the webcam is opened correctly
# if not cap.isOpened():
#    print("Could not open webcam")
#    exit()

# Read one frame from the webcam
# ret, frame = cap.read()

# If the frame was captured successfully, ret will be True

# if ret:
    # Save the captured frame as an image
#    cv2.imwrite("./output_images/captured_image.jpg", frame)
#    print("Image saved as captured_image.jpg")
# else:
#    print("Failed to capture image")

# Release the webcam
# cap.release()

# Close all OpenCV windows
# cv2.destroyAllWindows()
"""
