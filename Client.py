import socket
import select
import SenderSW
import ReceiverSW
import SenderGBN
import ReceiverGBN
import SenderSR
import ReceiverSR

# Build a list to store type of sender or receiver
senderList = [SenderSW,SenderGBN,SenderSR]
receiverList = [ReceiverSW,ReceiverGBN,ReceiverSR]

# Function to handle client operations
def my_client():
    # Get the client type
    print('Input client type-----')
    print('1.Stop and wait\n2.Go back N\n3.Selective repeat\n')
    fcpType = int(input('Enter choice = '))
    if(fcpType>3 or fcpType<1):
        fcpType = 1
    fcpType -= 1

    # Define server IP address
    server_ip='127.0.0.1'

    # Define server port address
    server_port=1232

    # Define server address
    server_address=(server_ip,server_port)

    # Initialize socket and connect with server
    client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(server_address)

    # Notify if connection is successfull
    print("This client is online now")

    # Take a client name as input and send it to server
    name=input('Enter client name (All online users will see this) : ')
    client.send(str.encode(name))

    # Get self port number from server
    addr = client.recv(1024)
    addr = addr.decode()
    senderAddress = int(addr)

    # Loop until client wants to go offline
    while(True):
        # Enter user's choice and progress accordingly
        # There are 3 choices - send data, just wait(for receiving) and close connection
        print('Input options-----\n1.Send data\n2.Just be online\n3.Close\n')
        choice=int(input('Enter option : '))

        # If user wants to send data, request server for that
        # Otherwise just wait
        # if user wants to close, notify server about it and then close
        if(choice==1):
            client.send(str.encode("request for sending"))
        elif(choice!=2):
            client.send(str.encode("close"))
            break

        # Initialize input and output event generators
        inputs=[client]
        output=[]

        # Wait until any input/output event or timeout occurs
        readable,writable,exceptionals=select.select(inputs,output,inputs,3600)
        
        # If input event is generated(any data/signal came from server), handle it
        for s in readable:
            # Receive and decode the data
            data=s.recv(1024)
            data=data.decode()

            # If no other client is connected with server, cancel sending request
            if(data=="No other client is available"):
                print(data)
                break

            # If this client got sending permission from server
            elif(data=="Sending permission granted-----"):
                # Print the permission notification
                print(data)
                s.send(str.encode('ok'))

                # Enter data file name where data is stored
                file_name=input('Enter data file name : ')

                # Receive available receiver list from server
                receiver_list=s.recv(1024).decode().split('$')

                # Print the list and choose one of them for data transfer
                print('Available clients-----')
                for index in range(0,(len(receiver_list)-1)):
                    print((index+1),'. ',receiver_list[index])
                inp=int(input('\nYour choice : '))
                inp-=1

                # Ensure that the choice is valid
                while(inp not in range(0,(len(receiver_list)-1))):
                    inp=int(input('Correctly input your choice : '))
                    inp-=1

                # Notify server about the choice
                s.send(str.encode(str(inp)))

                # Get receiver port from server
                receiverAddress = int(s.recv(1024).decode())

                # Initialize sender object
                my_sender=senderList[fcpType].Sender(client,name,senderAddress,receiver_list[index],receiverAddress,file_name)
                
                # Start transmission (using sender object)
                my_sender.transmit()

                # Get and print notification from server about data transfer complition
                data=s.recv(1024)
                data=data.decode()
                print(data)

            # If this client got receiving request
            else:
                # Print the receiver starting status
                print('Receiving data-----')

                # Input the file name where received data will be stored
                file_name=input('Enter file name where data will be written : ')
                s.send(str.encode("ok"))

                # Initialize receiver object
                receiverAddress = int(data)
                my_receiver=receiverList[fcpType].Receiver(client,name,senderAddress,receiverAddress,file_name)
                
                # Start data receiving through receiver object
                my_receiver.startReceiving()
        
        # If no data sent/received for an hour, again ask for user options(loop again)
        if not (readable or writable or exceptionals):
            continue

    # Close the client connection
    client.close()


if __name__=='__main__':
        my_client()    