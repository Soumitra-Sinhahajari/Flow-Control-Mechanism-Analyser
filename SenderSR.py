import socket
import random
import time
import threading
import ErrorDetectingSchemes
import PacketManager
import Analysis

# Define maximum window size
MAX_WINDOW_SIZE = 8

MAX_SEQUENCE_NUMBER = 16

# Define default data bytes in a packet
defaultDataPacketSize=46

# Define time-out time in seconds
timeOut=2

# Define file name where analyses will be stored
analysis_file_name='SR.txt'

# Store all the round-trip times
rttStore = []


class Sender:
    def __init__(self, connection, name:str, senderAddress:int, receiver_name:str, receiverAddress:int, fileName:str): 
        self.connection         = connection
        self.name               = name
        self.receiver           = receiver_name
        self.fileName           = fileName
        self.senderAddress      = senderAddress
        self.receiverAddress    = receiverAddress
        self.packetType         = {'data' : 0, 'ack' : 1, 'nak' : 2}
        self.timeoutEvent       = threading.Event()
        self.endTransmitting    = False
        self.front              = 0
        self.end                = 0
        self.window_size        = 0
        self.pktCount           = 0
        self.totalPkt           = 0
        self.current_window     = []
        self.packet_timer       = []
        for index in range(0,MAX_SEQUENCE_NUMBER):
            self.current_window.append(0)
            self.packet_timer.append(0)
        self.window_write_lock  = threading.Lock()
        self.oldestFrame        = 0


    # Function to check if the acknowledgement number lies within window
    def validACK(self,ack_no:int):
        # If Ack is valid, return true
        if((self.front<ack_no and ack_no<=self.end) or (self.end<self.front and self.front<ack_no) or (ack_no<=self.end and self.end<self.front)):
            return True
        # If Ack no lies outside range, return false
        else:
            return False


    # Function to handle packet resending
    def resendPackets(self):
        time.sleep(0.2)

        # Loop until end of transmission
        while (not self.endTransmitting) or (self.window_size>0):
            # If any packet was sent
            if(self.window_size>0):
                current_time = time.time()
                oldest_packet = 0
                max_waiting_time = 0
                temp = self.front
                while(temp!=self.end):
                    spent_time = (current_time - self.packet_timer[temp])
                    if(spent_time > max_waiting_time):
                        max_waiting_time = spent_time
                        oldest_packet = temp
                    temp = (temp+1)%MAX_SEQUENCE_NUMBER
                # front_waiting_time = (current_time-self.packet_timer[self.front])
                # If time-out occurs and there is a valid outstanding window
                # Resend the oldest packet again
                # Restart timer
                if(max_waiting_time > timeOut):
                    # Acquire the lock of window
                    self.window_write_lock.acquire()
                    if(self.current_window[oldest_packet]!=0):
                        self.connection.send(str.encode(self.current_window[oldest_packet].toBinaryString(46)))
                        print('PACKET ',oldest_packet,' RESENDED')
                        self.packet_timer[oldest_packet] = time.time()
                        self.totalPkt += 1

                    # Release the lock of the window
                    self.window_write_lock.release()


    # Function to handle data sending
    def sendData(self):
        time.sleep(0.2)

        # Notify about the start of sending
        print("\n",self.name," starts sending data to ",self.receiver,"\n")
        
        # open data file for reading
        file = open(self.fileName,'r')

        # Read data of size of frame from file
        data_frame = file.read(defaultDataPacketSize)

        # Loop until whole data is sent
        while data_frame:
            # If window is not full, send another packet
            if(self.window_size<MAX_WINDOW_SIZE):
                # Build packet using data, type and sequence number
                packet = PacketManager.Packet(self.senderAddress, self.receiverAddress, self.packetType['data'], self.end, data_frame)

                # Store current packet for re-transmission (if needed)
                self.current_window[self.end] = packet

                # Acquire window write lock
                self.window_write_lock.acquire()

                # Send the packet
                self.connection.send(str.encode(packet.toBinaryString(46)))

                # Print 'sent' status
                print("\nPACKET ",self.end," SENT TO CHANNEL")

                self.packet_timer[self.end] = time.time()

                # Increment end, window size and other parameters accordingly
                self.end = ((self.end+1)%MAX_SEQUENCE_NUMBER)
                self.window_size += 1
                self.pktCount += 1
                self.totalPkt += 1

                # Read next data frame
                data_frame = file.read(defaultDataPacketSize)

                # release window write lock
                self.window_write_lock.release()

            # If all data has been read, break
            if len(data_frame) == 0: break
        
        # Set the end-transmitting flag True
        self.endTransmitting = True

        # Close the data file
        file.close()


    # Function to handle acknowledgement receiving
    def receiveAck(self):
        time.sleep(0.2)

        # Loop until end-transmitting flag is not set (data sending not over)
        while (not self.endTransmitting) or (self.window_size>0):
            # If a packet is sent
            if(self.window_size>0): 
                # Wait and receive acknowledgement and build packet from that
                received = self.connection.recv(384).decode()
                packet=PacketManager.Packet.build(received)
            else: continue

            # If packet type is acknowledgement, do the following
            if packet.getType() == 1:
                # If packet has no error, do the following
                if(packet.hasError()==False):
                    # If ACK_NO == SEQ_NO then receive it, stop timer(set the internal flag of time-out event)
                    if self.validACK(packet.seqNo):
                        # Acquire lock for accessing window
                        self.window_write_lock.acquire()

                        # Update the window front and window size
                        # According to the cumulative acknowledgement
                        while(self.front!=packet.seqNo):
                            # Store round-trip time into the list
                            now = time.time()
                            rtt = (now - self.packet_timer[self.front])
                            rttStore.append(rtt)

                            print("PACKET ",self.front," HAS REACHED SUCCESSFULLY\n")
                            self.current_window[self.front]=0
                            self.front = ((self.front+1)%MAX_SEQUENCE_NUMBER)
                            self.window_size -= 1

                        # Release window access lock
                        self.window_write_lock.release()

                    else:
                        print("WRONG ACK DISCARDED")
                else:
                    print("ERRONEOUS ACK DISCARDED")
            
            # If NAK packet came
            elif packet.getType() == 2:
                # If packet has no error
                if not packet.hasError():
                    # If requested sequence number is within window
                    if self.validACK(packet.seqNo):
                        # Acquire lock for accessing window
                        self.window_write_lock.acquire()

                        # Resend the requested packet
                        if(self.current_window[packet.seqNo]!=0):
                            self.connection.send(str.encode(self.current_window[packet.seqNo].toBinaryString(46)))
                            print('PACKET ',packet.seqNo,' RESENDED from NAK')
                            self.packet_timer[packet.seqNo] = time.time()
                            self.totalPkt += 1

                        # Release window access lock
                        self.window_write_lock.release()
                    else:
                        print("WRONG NAK DISCARDED")
                else:
                    print("ERRONEOUS NAK DISCARDED")
            
            else: 
                print("RECEIVED PACKET IS NOT AN ACK")
       

    def transmit(self):
        # Receive 'start' packet from channel for synchronization
        inp=self.connection.recv(1024)

        # record the strating time
        startTime = time.time()
        
        # Initialize threads for send management
        sendingThread = threading.Thread(name="sendingThread", target=self.sendData)
        ackCheckThread = threading.Thread(name='ackCheckThread', target=self.receiveAck)
        resendingThread = threading.Thread(name="resendingThread",target=self.resendPackets)

        # Start the threads
        sendingThread.start()
        ackCheckThread.start()
        resendingThread.start()

        # Wait for threads to join(End transmission)
        sendingThread.join()
        ackCheckThread.join()
        resendingThread.join()

        now=time.time()

        self.connection.recv(1024)

        # Notify channel about the end of transmission
        self.connection.send(str.encode("end"))

        # Calculate total time taken and write analysis into file
        totalTime=(now-startTime)
        Analysis.storeReport(self.name, self.receiver, analysis_file_name, self.pktCount, self.totalPkt, totalTime, rttStore)