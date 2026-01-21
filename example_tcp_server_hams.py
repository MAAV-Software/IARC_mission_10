"""Example TCP socket server."""
import socket
import json

print("Hello World")

def handle_message(message_dict):
    corrected_dict = message_dict["message"]
    if(corrected_dict == "we playing a real diamond quarter your not even good enough to lick the dirt off my cleats"):
        send("watch it jerk")
        print("watch it jerk")

    if(corrected_dict == "shut up idiot"):
        send("moron")
        print("moron")

    if(corrected_dict == "scab eater"):
        send("butt sniffer")
        print("butt sniffer")

    if(corrected_dict == "pus licker"):
        send("fart smeller")
        print("fart smeller")

    if(corrected_dict == "you eat dog crap for breakfast geek"):
        send("you mix wheaties with your mommas toe jam")
        print("you mix wheaties with your mommas toe jam")
        
    if(corrected_dict == "you bob for apples in toilet and like it"):
        send("you play ball like a girl")
        print("you play ball like a girl")
    
    if(corrected_dict == "tomorrow noon at our field"):
        send("count on it pee drinking crap face")
        print("count on it pee drinking crap face")

    if(corrected_dict == "what did you say"):
        send("you heard me")
        print("you heard me")



# We playing a real diamond quarter your not even good enough to lick the dirt off my cleats

# 3Shut up idiot

# 5scab eater

# 7Pus licker

# 9You eat dog crap for breakfast geek

# 11You bob for apples in toilet and like it

# 13What did you say 

# 15Tomorrow noon at our field

# 16Get the buffalo butt breath lets go




#2 Watch it jerk
# 4Moron
# 6Butt sniffer
# 8Fart smeller
# 10You mix wheaties with your mommas toe jam
# 12You play ball like a girl
# 14You heard me
# 16Count on it pea drinking crap face


def send(message):
    """Test TCP Socket Client."""
    # create an INET, STREAMing socket, this is TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        # connect to the server
        sock.connect(("localhost", 8001))

        # send a message
        message = json.dumps({"message": message})
        sock.sendall(message.encode('utf-8'))



def main():
    """Test TCP Socket Server."""
    # Create an INET, STREAMing socket, this is TCP
    # Note: context manager syntax allows for sockets to automatically be
    # closed when an exception is raised or control flow returns.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        # Bind the socket to the server
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 8000))
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
            handle_message(message_dict)


if __name__ == "__main__":
    main()










