"""Example TCP socket client."""
import socket
import threading
import json
import queue
import sys
from roles.explorer import ExploreDrone

def main():

    # coords_list = []
    coords_list = queue.Queue()
    coords_list.put((1, 2))
    coords_list.put((0, 0))
    coords_list.put((6, 7))
    ExploreDrone("rpi2", 8000, coords_list)


if __name__ == "__main__":
    main()