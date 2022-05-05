import socket
import time
import threading
import PacketManager
import Analysis

# Define default data bytes in a packet
defaultDataPacketSize=46

# Define time-out time in seconds
timeOut=2

# Define file name where analyses will be stored
analysis_file_name='SWARQ.txt'

# Store all the round-trip times
rttStore = []

# Define Sender class for data sending management
class Sender:
    # Function for initializing sender object
    def __init__(self, connection, name:str, senderAddress:int, receiver_name:str, receiverAddress:int, fileName:str):
        # Get the client/sender connection and other informations (name, receive name, data file name)
        self.connection=connection 
        self.name               = name
        self.receiver           = receiver_name
        self.fileName           = fileName
        self.senderAddress      = senderAddress
        self.receiverAddress    = receiverAddress

        # Define transmission management variables (packet type, timeout-event, sequence no and other flags)
        self.packetType         = {'data' : 0, 'ack' : 1}
        self.endTransmitting    = False
        self.seqNo              = 0
        self.pktCount           = 0
        self.totalPktCount      = 0
        self.pktSent            = False
        self.sentTime           = 0
        self.receiveTime        = 0
        self.send_lock          = threading.Lock()


    # Function to resend data when time-out occurs and restart sent-timer
    #def resendCurrentPacket(self):
    #    self.connection.send(str.encode(self.recentPacket.toBinaryString(46)))
    #    self.sentTime = time.time()


    # Function to handle packet resending
    def resendPackets(self):
        time.sleep(0.2)

        # Loop until end of transmission
        while((not self.endTransmitting) or self.pktSent):
            # If any packet was sent
            if(self.pktSent):
                current_time = time.time()
                waiting_time = (current_time-self.sentTime)
                # If time-out occurs and there is a valid outstanding window
                # Resend all the packets in the window again
                # Restart timer (Clear internal flag of Event object)
                if(waiting_time > timeOut):
                    self.send_lock.acquire()
                    self.connection.send(str.encode(self.recentPacket.toBinaryString(46)))
                    self.sentTime = time.time()
                    print('PACKET ',self.pktCount,' RESENDED')
                    self.totalPktCount += 1
                    self.send_lock.release()



    # Function to send data
    def sendData(self):
        time.sleep(0.2)

        # Notify about the start of sending
        print("\n",self.name," starts sending data to ",self.receiver,"\n")
        
        # open data file for reading
        file = open(self.fileName,'r')

        # Read data of size of frame from file
        data_frame = file.read(defaultDataPacketSize)
        
        # Initialize sequence number and other variables
        self.seqNo = 0
        self.pktCount = 0
        self.totalPktCount = 0

        # Loop until whole data is sent
        while data_frame:
            if(not self.pktSent):
                # Build packet using data, type and sequence number
                packet = PacketManager.Packet(self.senderAddress, self.receiverAddress, self.packetType['data'], self.seqNo, data_frame)

                # Store current packet for re-transmission (if needed)
                self.recentPacket = packet

                self.send_lock.acquire()

                # Send the packet and start sent-timer
                self.connection.send(str.encode(packet.toBinaryString(46)))
                self.sentTime = time.time()
            
                # Make packet sent flag true
                self.pktSent = True

                # Increment sequence number and other parameters accordingly
                self.seqNo = (self.seqNo+1)%2
                self.pktCount += 1
                self.totalPktCount += 1

                # Print 'sent' status
                print("\nPACKET ",self.pktCount," SENT TO CHANNEL")

                # Release the send lock
                self.send_lock.release()

                # Read next data frame
                data_frame = file.read(defaultDataPacketSize)

                # If all data has been read, break
                if len(data_frame) == 0: break
        
        # Set the end-transmitting flag True
        self.endTransmitting = True

        # Close the data file
        file.close()
        

    # Function to receive ACK packets
    def receiveAck(self):
        time.sleep(0.2)

        # Loop until end-transmitting flag is not set (data sending not over)
        while((not self.endTransmitting) or (self.pktSent)):
            # If a packet is sent
            if self.pktSent: 
                # Wait and receive acknowledgement and build packet from that
                received = self.connection.recv(384).decode()
                packet=PacketManager.Packet.build(received)
            else: continue

            # If packet type is acknowledgement, do the following
            if packet.getType() == 1:
                # If packet has no error, do the following
                if(packet.hasError()==False):
                    # If ACK_NO == SEQ_NO then receive it, stop timer(set the internal flag of time-out event)
                    if packet.seqNo == self.seqNo:
                        # Store the round trip time
                        self.receiveTime = time.time()
                        rtt = (self.receiveTime - self.sentTime)
                        rttStore.append(rtt)

                        # Unset the pktSent flag
                        print("PACKET HAS REACHED SUCCESSFULLY\n")
                        self.pktSent = False 
                    else:
                        print("WRONG ACK DISCARDED")
                else:
                    print("ERRONEOUS ACK DISCARDED")
            else: 
                print("RECEIVED PACKET IS NOT AN ACK")
            

    # Function to control the whole transmission
    def transmit(self):
        # Receive 'start' packet from channel for synchronization
        inp=self.connection.recv(1024)

        # record the strating time
        startTime=time.time()

        # Create a thread to handle data sending
        sendingThread = threading.Thread(name="sendingThread", target=self.sendData)

        # Create packet resending thread
        resendingThread = threading.Thread(name="resendingThread",target=self.resendPackets)
        
        # Create another thread to handle acknowledgement receiving
        ackCheckThread = threading.Thread(name='ackCheckThread', target=self.receiveAck)

        # Start both the threads
        sendingThread.start()
        ackCheckThread.start()
        resendingThread.start()

        # Wait for the threads to join (End their task)
        sendingThread.join()
        ackCheckThread.join()
        resendingThread.join()

        # Notify channel about the end of transmission
        self.connection.send(str.encode("end"))

        # Calculate total time taken and write analysis into file
        now=time.time()
        totalTime=(now-startTime)
        Analysis.storeReport(self.name, self.receiver, analysis_file_name, self.pktCount, self.totalPktCount, totalTime, rttStore)