import socket
import time
import PacketManager

# Define Receiver class to handle data receiving 
class Receiver:
    # Function to initialize obect
    def __init__(self, connection, name:str, senderAddress:int, receiverAddress:int, file:str):
        # Get the client/receiver connection and other informations (name, data file name)
        self.connection         = connection
        self.name               = name
        self.file_name          = file
        self.senderAddress      = senderAddress
        self.receiverAddress    = receiverAddress

        # Define receiver management variables (packet type, sequence no and other flags)
        self.packetType         = {'data' : 0, 'ack' : 1}
        self.seqNo              = 0
        self.recentACK          = PacketManager.Packet(senderAddress, receiverAddress, 1, 0, "Acknowledgement Packet")


    # Function for building and sending acknowledgement packet
    def sendAck(self):
        packet = PacketManager.Packet(self.senderAddress, self.receiverAddress, self.packetType['ack'],self.seqNo,'acknowledgement Packet')
        self.recentACK = packet
        self.connection.send(str.encode(packet.toBinaryString(22)))
    

    # Function for resending previous acknowledgement packet if needed
    def resendPreviousACK(self):
        self.connection.send(str.encode(self.recentACK.toBinaryString(22)))
  

    # Function for receiving data
    def startReceiving(self):
        time.sleep(0.4)

        # Wait for data and receive
        data=self.connection.recv(576).decode()

        total_data=''

        # If data-receiving hasn't ended yet 
        while data!='end':
            # Build packet from binary data string
            packet = PacketManager.Packet.build(data)
            print("\nPACKET RECEIVED")
            
            # If packet has no error
            if not packet.hasError():
                print("NO ERROR FOUND")
                # Get packet sequence number 
                seqNo = packet.getSeqNo()

                # If sequence number is equal to required one write the data into specified file
                # And send the corresponding ACK
                if self.seqNo == seqNo:
                    
                    data = packet.getData()
                    # print(data)
                    total_data += data
                    self.seqNo = (self.seqNo+1) % 2
                    self.sendAck()
                    print("ACK SENT FROM RECEIVER\n")

                # If sequence number is not what is required, resend the previous ACK 
                else:
                    self.resendPreviousACK()
                    print("ACK RESENDED")
            # Discard erroneous packet
            else:
                print("PACKET DISCARDED")

            # Wait and receive next packet
            data=self.connection.recv(576).decode()

        # print(total_data)
        file = open(self.file_name,'a')
        file.write(total_data)
        file.close()