import socket
import time
import PacketManager
import threading

# Define window size
WINDOW_SIZE = 8

# define maximum sequence number
MAX_SEQUENCE_NUMBER = 16

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
        self.packetType         = {'data' : 0, 'ack' : 1, 'nak' : 2}
        self.front              = 0
        self.end                = WINDOW_SIZE
        self.window             = []
        self.filled_up          = []
        for index in range(0,MAX_SEQUENCE_NUMBER):
            self.window.append(0)
            self.filled_up.append(False)
        self.NAK_sent           = False
        self.ACK_needed         = False
        self.recentACK          = PacketManager.Packet(self.senderAddress, self.receiverAddress, 1, 0, "Acknowledgement Packet")
        self.endReceiving       = False
        self.lastACKsent        = 'not started'


    # Function to check if the acknowledgement number lies within window
    def validSEQ(self,seq_no:int):
        # If Ack is valid, return true
        if((self.front<=seq_no and seq_no<self.end) or (self.end<self.front and self.front<=seq_no) or (seq_no<self.end and self.end<self.front)):
            return True
        # If Ack no lies outside range, return false
        else:
            return False


    # Function for building and sending acknowledgement packet
    def sendAck(self):
        packet = PacketManager.Packet(self.senderAddress, self.receiverAddress, self.packetType['ack'],self.front,'acknowledgement Packet')
        self.recentACK = packet
        print('Sent ACK no = ',self.front)
        self.connection.send(str.encode(packet.toBinaryString(22)))
        self.lastACKsent = time.time()


    # Function for building and sending no acknowledgement packet
    def sendNak(self):
        packet = PacketManager.Packet(self.senderAddress, self.receiverAddress, self.packetType['nak'],self.front,'No acknowledgement')
        self.connection.send(str.encode(packet.toBinaryString(22)))
        print('Sent NAK no = ',self.front)


    # Function for resending previous acknowledgement packet if needed
    def resendPreviousACK(self):
        # this is the acknowledgement timer
        # resend the last acknowledgement if timeout occurs
        while(not self.endReceiving):
            if(self.lastACKsent=='not started'):
                continue
            current_time = time.time()
            total_spent = (current_time - self.lastACKsent )
            if(total_spent > 1):
                self.connection.send(str.encode(self.recentACK.toBinaryString(22)))
                self.lastACKsent = time.time()
  

    # Function for receiving data
    def startReceiving(self):
        time.sleep(0.4)

        ACKresendingThread = threading.Thread(target=self.resendPreviousACK)
        ACKresendingThread.start()

        # Wait for data and receive
        data=self.connection.recv(576).decode()

        total_data = ''

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

                # If packet other than first one got, send NAK
                if(seqNo!=self.front and self.NAK_sent==False):
                    self.sendNak()
                    self.NAK_sent = True
                
                # If seq no if within the window accept it
                # Store the data and flags appropiately
                if(self.validSEQ(seqNo) and self.filled_up[seqNo]==False):
                    self.filled_up[seqNo] = True
                    self.window[seqNo] = packet.getData()
                    #print(packet.getData())

                    # Take the received data sequentially into the final data string
                    # Update the front, end of the window accordingly (also update flags)
                    while(self.filled_up[self.front]==True):
                        total_data += self.window[self.front]
                        self.filled_up[self.front] = False
                        self.front = (self.front + 1)%MAX_SEQUENCE_NUMBER
                        self.end = (self.end + 1)%MAX_SEQUENCE_NUMBER
                        self.ACK_needed = True
                        print('PACKET RECEIVED SUCCESSFULLY')

                    # If sequential packet received, send acknowledgement
                    if(self.ACK_needed):
                        self.sendAck()
                        self.ACK_needed = False
                        self.NAK_sent = False
            
            # Discard erroneous packet
            else:
                print("PACKET DISCARDED")

            # Wait and receive next packet
            data=self.connection.recv(576).decode()

        # Stop the resending-acknowledgement thread
        self.endReceiving = True
        ACKresendingThread.join()

        # Write the whole data into file
        file = open(self.file_name,'a')
        file.write(total_data)
        file.close()

        