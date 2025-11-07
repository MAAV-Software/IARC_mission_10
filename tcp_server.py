"""Example TCP socket server."""
import socket
import json
import threading

class MainDrone:
    "Construct an instance of the main drone"

    def __init__(self, host, port):
        """Construct a Manager instance and start listening for messages."""

        self.host = host
        self.port = port
        self.coords = []

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

            while True:
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
        else:
            print("Message Unknown")
        
    # adds one pair of coords
    def handle_coordinates(self, message_dict):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(("rpi2", 8000)) 
            self.coords.append(message_dict["coords"])
            message = json.dumps({
                "message_type": "coords_ack"
            })
            sock.sendall(message.encode('utf-8'))
            print(self.coords)

    def run_drone(self):
        tcp_thread = threading.Thread(target=self.tcp_server)
        tcp_thread.start()
        tcp_thread.join()
        


def main():
    """Test TCP Socket Server and git access from RPi"""
    # Create an INET, STREAMing socket, this is TCP
    # Note: context manager syntax allows for sockets to automatically be
    # closed when an exception is raised or control flow returns.
    MainDrone("rpi1", 8000)


if __name__ == "__main__":
    main()
