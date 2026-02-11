"""Example TCP socket server."""
import socket
import json

def send(message):
    """Test TCP Socket Client."""
    # create an INET, STREAMing socket, this is TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        # connect to the server
        # TODO: add ip address
        sock.connect(("localhost", 8000))

        # send a message
        message = json.dumps({"message": message})
        sock.sendall(message.encode('utf-8'))

def handle_message(message_dict):
    msg = message_dict["message"]
    x, y = msg.strip().split(',')
    print(x,y)
    return x,y 

    # message = message_dict["message"]
    
    # file_path = 'results.txt' 
    # try:
    #     with open(file_path, 'r') as file:
    #         content = file.readlines()
    #         # print(content)
    # except FileNotFoundError:
    #     print(f"Error: The file '{file_path}' was not found.")
    # except Exception as e:
    #     print(f"An error occurred: {e}")


    # #identify number in message 
    # index = message.index(" ")

    
    # number = message[index+1:]
    # print(number)
    # try:
    #     message_back = content[int(number)].strip()
    #     print("sent "+ message_back)
    #     send(message_back)
    # except:
    #     pass
    #return section of content betwen "/n" and includes number
    


def main():

    all_coords = []
    
    with open("results.txt", 'r') as file:
        for line in file:
        # Find all numbers (including negatives and decimals)
        # Regex explanation:
        # -?    -> optional negative sign
        # \d+   -> one or more digits
        # \.    -> a literal decimal point
        # \d+   -> one or more digits after the decimal
            p1, p2, p3, p4, p5, p6 = line.strip().split(' ')
            x = p5[2:-1]
            y = p6[2:] 
            print(x, y, "\n")
            all_coords.append([x, y])


    """Test TCP Socket Server."""
    # Create an INET, STREAMing socket, this is TCP
    # Note: context manager syntax allows for sockets to automatically be
    # closed when an exception is raised or control flow returns.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        # Bind the socket to the server
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", 8001))
        sock.listen()

        # Socket accept() will block for a maximum of 1 second.  If you
        # omit this, it blocks indefinitely, waiting for a connection.
        sock.settimeout(1)

        #send("JEIOSHDFKJL:SH 1")
        
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
            if(message_dict["message"] == "Amin has no middle name"):
                break
            else:
                x,y = handle_message(message_dict)
                all_coords.append((x,y))
            
    with open("DervinsGOUToutBREAK.txt", 'w') as file: 
        for item in all_coords:
            file.write(f"{item}\n")

if __name__ == "__main__":
    main()
