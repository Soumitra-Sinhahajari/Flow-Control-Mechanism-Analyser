import ErrorDetectingSchemes

# Define packet structure and functionalities
class Packet:
    # Function for initialization of a packet
    def __init__(self, source:int, destination:int, _type:int, seqNo:int, segmentData:str):
        # Get source address
        self.source = source

        # Get destination address
        self.destination = destination

        # Get type of packet
        self.type = _type 

        # Get packet data
        self.segmentData = segmentData
        
        # Get packet sequence number
        self.seqNo = seqNo

    #  preamble + sfd + dest + source + type + seqNo + data +  crc
    #     7     +  1  +  6   +   6    +  1   +   1   +  46  +   4  =  72

    # Function to convert packet into binary string
    def toBinaryString(self, data_size:int):
        # Initialize preamble and sfd
        preamble = '01'*28 
        sfd = '10101011' 

        # Convert source and destination address into binary strings
        destAddress = '{0:048b}'.format(self.destination)
        sourceAddress = '{0:048b}'.format(self.source)

        # Convert packet type into 8 bit binary string
        typeToBits = '{0:08b}'.format(self.type)

        # Convert sequence no into 8 bit binary string
        seqToBits = '{0:08b}'.format(self.seqNo)

        segmentData = self.segmentData
        # Pad the segment data if needed
        if(len(segmentData)<data_size):
            segmentData += '\0'*(data_size-len(segmentData))

        # For each character in data, convert into equivalent ASCII code and build the final binary string
        data = ""
        for i in range(0, len(segmentData)):
            character = segmentData[i]
            dataByte = '{0:08b}'.format(ord(character))
            data = data + dataByte

        # Add the parts to get the final packet
        packet = preamble + sfd + destAddress + sourceAddress + typeToBits + seqToBits + data 

        # Calculate CRC-16 on this   
        crc = ErrorDetectingSchemes.calculate_code("CRC",packet)
        
        # Append CRC-16 at the end of the packet
        packet = packet + crc
        self.packet = packet

        # Return packet
        return packet


    # Function to convert binary string into packet object
    @classmethod
    def build(cls,packet):
        # Get source and destination addresses
        source = int(packet[64:112],2)
        destination = int(packet[112:160],2)

        # Get type of packet
        _type=int(packet[160:168],2)

        # Get sequence number of packet
        seq_no=int(packet[168:176],2)

        # For data part
        # Break string into 8-bit parts
        # For each such 8-bit binary string find the equivalent ASCII character
        # Append it into result
        text = ""
        data = packet[176:-32]
        asciiData = [data[i:i+8] for i in range(0,len(data),8)]
        for letter in asciiData:
            # Skip padded null data
            if(letter=='00000000'):
                continue
            text += chr(int(letter,2))

        # Initialize new packet with above elements and return it
        new_packet = cls(source,destination,_type,seq_no,text)
        new_packet.packet = packet
        return new_packet
    
    # Function to extract data
    def getData(self):
        return self.segmentData
    
    # Function to extract type
    def getType(self):
        return self.type

    # Function to extract sequence number
    def getSeqNo(self):
        return self.seqNo

    # Function to check error using binary string formed packet
    def hasError(self):
        return ErrorDetectingSchemes.check_error("CRC",self.packet)

# Just testing
if __name__=='__main__':
    seq=int(input('Enter sequence number : '))
    _type=int(input('Enter type of the packet : '))
    data=input('Enter 46 character string : ')
    packet=Packet(_type,seq,data)
    new_=packet.toBinaryString()
    new_=str.encode(new_)
    new_=new_.decode()
    new_packet=Packet.build(new_)
    print('Data : ',new_packet.getData())
    print('Sequence number : ',new_packet.getSeqNo())
    print('Type : ',new_packet.getType())
    if(new_packet.hasError()==False):
        print('No error')
