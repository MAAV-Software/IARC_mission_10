"""Example TCP socket server."""
import socket
import json
import threading
import pathlib

class ManagerDrone:
    "Construct an instance of the main drone"

    def __init__(self, host, port):
        """Construct a Manager instance and start listening for messages."""

        self.host = host
        self.port = port
        self.bounds = [ # Goes in order top left, top right, bottom left, bottom right
            (-3.613, 0.855),
            (-3.613, 7.051),
            (0.7646, 0.855),
            (0.7646, 7.051),
        ] # These can be hard-coded, as we will be allowed to gather these coordinates beforehand
        self.coords = []
        self.exp_drones = {}
        self.finished_drones = 0
        self.shutdown_flag = False

        self.run_drone()


    def tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            # Bind the socket to the server
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen()

            # Socket accept() will block for a maximum of 1 second.  If you
            # omit this, it blocks indefinitely, waiting for a connection.
            sock.settimeout(1)

            while not self.shutdown_flag:
                # Wait for a connection for 1s.  The socket library avoids consuming
                # CPU while waiting for a connection.
                try:
                    clientsocket, address = sock.accept()
                except socket.timeout:
                    continue
                print("Connection from", address[0])

                # Socket recv() will block for a maximum of 1 second.  If you omit
                # this, it blocks indefinitely, waiting for packets.
                clientsocket.settimeout(1)

                # Receive data, one chunk at a time.  If recv() times out before we
                # can read a chunk, then go back to the top of the loop and try
                # again.  When the client closes the connection, recv() returns
                # empty data, which breaks out of the loop.  We make a simplifying
                # assumption that the client will always cleanly close the
                # connection.
                with clientsocket:
                    message_chunks = []
                    while True:
                        try:
                            data = clientsocket.recv(4096)
                        except socket.timeout:
                            continue
                        if not data:
                            break
                        message_chunks.append(data)

                # Decode list-of-byte-strings to UTF8 and parse JSON data
                message_bytes = b''.join(message_chunks)
                message_str = message_bytes.decode("utf-8")

                try:
                    message_dict = json.loads(message_str)
                except json.JSONDecodeError:
                    continue
                print(message_dict)
                self.handle_message(message_dict)
    
    def handle_message(self, message_dict):
        if message_dict["message_type"] == "coordinates":
            self.handle_coordinates(message_dict)
        elif message_dict["message_type"] == "registration":
            self.handle_registration(message_dict)
        elif message_dict["message_type"] == "finished":
            self.handle_finished(message_dict)
        else:
            print("Message Unknown")
        
    # adds one pair of coords
    def handle_coordinates(self, message_dict):
        worker_host = message_dict["host"]
        worker_port = message_dict["port"]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((worker_host, worker_port)) 
            self.coords.append(message_dict["coords"])
            message = json.dumps({
                "message_type": "coords_ack"
            })
            sock.sendall(message.encode('utf-8'))
    
    def handle_registration(self, message_dict):
        drone_host = message_dict["drone_host"]
        drone_port = message_dict["drone_port"]
        drone_key = str(drone_host) + str(drone_port)
        self.exp_drones[drone_key] = {
            "drone_host": drone_host,
            "drone_port": drone_port,
            "status": "working"
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((drone_host, drone_port)) 
            message = json.dumps({
                "message_type": "registration_ack"
            })
            sock.sendall(message.encode('utf-8'))

    def handle_finished(self, message_dict):
        drone_host = message_dict["drone_host"]
        drone_port = message_dict["drone_port"]
        drone_key = str(drone_host) + str(drone_port)
        if self.exp_drones[drone_key]["status"] == "working":
            self.exp_drones[drone_key]["status"] = "finished"
            self.finished_drones += 1
            if self.finished_drones == len(self.exp_drones):
                self.shutdown_flag = True
        else:
            print("Error: Received a 'finished' message from a finished worker")
            exit(1)

    def run_drone(self):
        tcp_thread = threading.Thread(target=self.tcp_server)
        tcp_thread.start()
        tcp_thread.join()

        current_dir = pathlib.Path(__file__).parent
        root_dir = current_dir.parent.parent
        output_dir = root_dir / "output"
        mapreduce_dir = root_dir / "mapreduce"
        output_dir.mkdir(exist_ok=True)  # creates folder if missing
        file_path = output_dir / "output-0.txt"
        bound_path = mapreduce_dir / "world_bounds.txt"

        with open(bound_path, "w") as f: # Clear the output file
            pass
        with open(bound_path, "a") as f: # Write the world bounds into it
            for bound in self.bounds:
                f.write(f"{bound[0]} {bound[1]}\n")

        with open(file_path, "w") as f: # Clear the output file
            pass
        with open(file_path, "a") as f: # Write the coords into it
            for coord in self.coords:
                f.write(f"{coord[0]} {coord[1]} {coord[2]} {coord[3]} {coord[4]} {coord[5]} {coord[6]} {coord[7]}\n")
    
            
