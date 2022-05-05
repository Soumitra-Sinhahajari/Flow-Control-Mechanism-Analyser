# Define word size (1 Byte here)
word=8

# CRC polynomial (CRC-32-IEEE 802.3)
crc='100000100110000010001110110110111'

# Function to XOR two bit strings
def xor(a:str,b:str):
    length=len(a)
    result=''

    # XOR the equal-sized strings bitwise
    for index in range(0,length):
        if(a[index]==b[index]):
            result+='0'
        else:
            result+='1'

    # Return result
    return result


# Function to calculate division modulo 2
def division_modulo_2(divident:str):
    # Get the length of CRC generator
    length=len(crc)

    # Calculate the remainder using division
    # divide the divident into substrings of length of CRC generator
    # Consecutively XOR it with CRC generator to find remainder and add next bit and repeat
    result=divident[0:length]
    for index in range(length,len(divident)):

        # If remainder starts with '1' divide with CRC generator otherwise with 0's of length of that
        # In either case 1st bit of next remainder will be zero, so delete that
        if result[0] == '1':
            result = xor(result,crc)[1:] + divident[index]
        else:
            result = xor(result,'0'*length)[1:] + divident[index]

    # Last XORing was skipped in loop(to prevent error) so do  it here
    if result[0] == '1':
        result = xor(result,crc)[1:]
    else:
        result = xor(result,'0'*length)[1:]

    # Return result
    return result


# Array of error detecting functions pointers
error_detecting_codes={'CRC':division_modulo_2}


# Function to calculate specific detecting codes at sender side
def calculate_code(name:str,data:str):
    if(name=='CRC'):
        data+='0'*(len(crc)-1)

    # Return the appropiate function which indeed returns the code
    return error_detecting_codes[name](data)


# Function to detect error using specific code if possible and return false if no error detected
def check_error(name:str,data:str):
    if(int(error_detecting_codes[name](data))==0):
        return False
    return True
        


if __name__=='__main__':
    # Input the data
    data=input('Input data to be evaluated = ')

    # Print the specific error detecting codes and if error is detected at receiver or not
    print('Detecting codes-----')
    result=''
    temp=''
    msg='No error'

    # CRC
    result=calculate_code('CRC',data)
    print('Calculated CRC = ',result)
    temp=data+result
    if(check_error('CRC',temp)==False):
        print(msg)