"""Example TCP socket client."""
import os
import cv2
import pathlib
import socket
from ultralytics import YOLOWorld
from roles.explorer import ExploreDrone

input_path = "DervinSmellsLikePoop.csv"

def main():

    hostname = socket.gethostname()
    print(hostname)

    coords_list = []
    with open(input_path, "r") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            line_contents = line.strip().split(',')
            coords_list.append(( float(line_contents[0]), float(line_contents[1]) ))

    ExploreDrone("localhost", 8001, "localhost", 8000, coords_list) # For now, just simulating on one laptop, so same hostname for both manager and explorer
    # ExploreDrone("192.168.1.22", 8001, "192.168.1.22", 8000, coords_list)

if __name__ == "__main__":
    main()