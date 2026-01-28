"""Example TCP socket server."""
import socket
import json

print("Hello World")

with open('amin_swati.txt', 'r') as file:
    lines = file.readlines() #lines is a list

def handle_message(message_dict):
    corrected_dict = message_dict["message"].strip()
    print(corrected_dict)
    if(corrected_dict == "JEIOSHDFKJL:SH 1"):
        send(lines[0])
        print(lines[0])

    if(corrected_dict == "JEIOSHDFKJL:SH 2"):
        send(lines[1])
        print(lines[1])

    if(corrected_dict == "JEIOSHDFKJL:SH 3"):
        send(lines[2])
        print(lines[2])

    if(corrected_dict == "JEIOSHDFKJL:SH 4"):
        send(lines[3])
        print(lines[3])
    
    if(corrected_dict == "JEIOSHDFKJL:SH 5"):
        send(lines[4])
        print(lines[4])

    if(corrected_dict == "JEIOSHDFKJL:SH 6"):
        send(lines[5])
        print(lines[5])
    
    if(corrected_dict == "JEIOSHDFKJL:SH 7"):
        send(lines[6])
        print(lines[6])
    
    if(corrected_dict == "JEIOSHDFKJL:SH 8"):
        send(lines[7])
        print(lines[7])
    
    if(corrected_dict == "JEIOSHDFKJL:SH 9"):
        send(lines[8])
        print(lines[8])

    if(corrected_dict == "JEIOSHDFKJL:SH 10"):
        send(lines[9])
        print(lines[9])
        
    if(corrected_dict == "JEIOSHDFKJL:SH 11"):
        send(lines[10])
        print(lines[10])

    if(corrected_dict == "JEIOSHDFKJL:SH 12"):
        send(lines[11])
        print(lines[11])
    
    if(corrected_dict == "JEIOSHDFKJL:SH 13"):
        send(lines[12])
        print(lines[12])
    
    if(corrected_dict == "JEIOSHDFKJL:SH 14"):
        send(lines[13])
        print(lines[13])

    if(corrected_dict == "JEIOSHDFKJL:SH 15"):
        send(lines[14])
        print(lines[14])

    if(corrected_dict == "JEIOSHDFKJL:SH 16"):
        send(lines[15])
        print(lines[15])



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
    with open('amin_swati.txt', 'w') as file:
        for i in range(1,17):
            file.write("Message "+ str(i) + "\n")
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










