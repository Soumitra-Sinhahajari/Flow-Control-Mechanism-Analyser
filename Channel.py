import socket
import select
import threading
import ErrorInsertion
import random
import time

# Dictionary to store each connection information i.e. - ' address : [connection,name] '
client_map={}

# Dictionary to store current state of a client i.e. - ' address : state '
# 0 indicates either it's idle or sending data
# 1 indicates it's working as a receiver
receiver_index={}

# Define the lock object
my_lock=threading.Lock()

# Function to select if original packet or tainted packet or no packet will be sent
def process_packet(packet:str):
    # Randomly generate what would be done
    flag=random.randint(0,100)

    # If flag is 0-70, original packet will be sent
    # If flag is 71-80, taint the packet and send
    # If flag is 81-99, drop the packet
    if(flag>=0 and flag<70):
        return packet
    elif(flag>=70 and flag<80):
        return ErrorInsertion.insert_error(packet)
    elif(flag>=80 and flag<90):
        time.sleep(0.5)
        return packet
    else:
        return ''


# Function to handle channel actions for data passing
def channel(sender,receiver):
    # Initialize lists of input and output event generators
    inputs=[sender,receiver]
    outputs=[]
    data='start'

    # Tell sender to start transmitting
    sender.send(str.encode('start'))

    # loop until all data is sent from sender to receiver
    while(data!="end"):
        # Wait for an event (Data come from sender/Ack come from receiver)
        readable, writable, exceptionals=select.select(inputs,outputs,inputs)

        # Handle the incoming data
        for s in readable:
            # If data was sent by sender, deliver it to receiver (vice-versa)
            if s is sender:
                # Receive, decode and process the data packet
                data=s.recv(576)
                data=data.decode()
                new_data=''
                if(data!="end"):
                    new_data=process_packet(data)
                if(data=="end"):
                    receiver.send(str.encode(data))
                elif(new_data!=''):
                    receiver.send(str.encode(new_data))
            if s is receiver:
                data=s.recv(384)
                data=data.decode()
                new_data=''
                new_data=process_packet(data)
                if(new_data!=''):
                    sender.send(str.encode(new_data))

        # If any error occurs in sender/receiver connection, close that connection
        for s in exceptionals:
            inputs.remove(s)
            s.close()


# Function for controlling data passing using thread lock
def send_handler(client,address):
    # Check if any other client is connected or not
    if(len(client_map.keys())==1):
        client.send(str.encode("No other client is available"))
        return
    
    # Try to get the lock for data transfer
    my_lock.acquire()
    
    # Notify sender that lock acquired
    client.send(str.encode("Sending permission granted-----"))
    # Just a simple sender reply
    inp=client.recv(1024)
    
    # Get all available client addresses
    dummy=list(client_map.keys())
    
    # Remove it's own address from the list
    dummy.remove(address)
    
    # Convert all addresses into '$' separated string
    total=''
    for index in range(0,len(dummy)):
        total+=(client_map[dummy[index]][1]+'$')
    
    # Send the available clients list to sender for choosing it's client
    client.send(str.encode(str(total)))
    
    # Get sender choice
    inp=client.recv(1024)
    inp=int(inp.decode())
    
    # Get the receiver connection from address
    receiver=client_map[dummy[inp]][0]
    recv_addr=dummy[inp]

    # Send receiver address to sender
    client.send(str.encode(str(recv_addr[1])))

    # Notify receiver about this and change it's state to receiving
    receiver.send(str.encode(str(address[1])))
    receiver_index[dummy[inp]]=1

    # Wait for receiver 'ok' reply
    inp=receiver.recv(1024)

    # Print sender and receiver info
    print(address,' is sending data to ',recv_addr)

    # Complete data transfer using channel
    channel(client,receiver)

    # Print end of data transfer
    print(address,' ended transferring data to ',recv_addr)
    
    # Notify sender about completion
    client.send(str.encode("Sending permission revoked-----"))
    
    # Change receiver state to idle/sending
    receiver_index[recv_addr]=0

    # Release lock
    my_lock.release()


# Function for run method of client thread
def client(connection,address):
    inputs=[connection]
    output=[]
    data="start"

    while data!="close":
        # Wait for an event (Data come from sender)
        readable, writable, exceptionals=select.select(inputs,output,inputs)

        # Check if client is serving as a receiver
        # If it is, skip processing the packets
        if(receiver_index[address]==1):
            continue

        # Handle the incoming data
        for s in readable:
            # Receive, decode and the data
            data=s.recv(1024)
            data=data.decode()

            # Get the client request and process it accordingly
            if data=="request for sending":
                send_handler(connection,address)

        # If any error occurs in sender/receiver connection, close that connection
        for s in exceptionals:
            inputs.remove(s)
            s.close()

    # Close the connection
    connection.close()

    # Remove map and list entries
    client_map.pop(address)
    receiver_index.pop(address)

    # Notify client's leaving
    print(address,' is leaving')


# Function to specify server functionality
def server():
    # Defien server IP address
    server_ip='127.0.0.1'
    # Define server port address
    server_port=1232
    # Define total server address
    server_address=(server_ip,server_port)

    # Initialize server
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    # Bind server to the address
    server.bind(server_address)

    # Define maximum waiting client requests
    server.listen(5)

    # Notify that server started
    print("Server started")

    # Put server on listen mode and accept client requests
    while True:
        # Accept client request
        new_connection,address=server.accept()
        
        # Notify client's joining
        print(address,' joined')

        # Receive client name from client and send port-number to it
        name=new_connection.recv(1024)
        name=name.decode()
        new_connection.send(str.encode(str(address[1])))

        # Update client_map and receiver_index list with the new client
        client_map[address]=[new_connection,name]
        receiver_index[address]=0

        # Define and start new client thread
        new_thread=threading.Thread(target=client,args=(new_connection,address))
        new_thread.start()


# Main function
if __name__=='__main__':
    server()