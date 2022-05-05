import random


def alter_bit(data:str,index:int):
    # Make a list
    temp=list(data)

    # Alter bit at desired position
    if(temp[index]=='1'):
        temp[index]='0'
    else:
        temp[index]='1'

    # Rebuild the string and return it
    data=''.join(temp)
    return data


def insert_error(data:str):
    # get length of the data
    length=len(data)

    # Initialize erroneous data string
    altered_data=data

    # Randomly generate the number of bits to be altered
    total=random.randint(1,length)

    # For all the bits to be altered
    # Generate random position
    # Alter the bit at that position
    for i in range(0,total):
        index=random.randint(0,(length-1))
        altered_data=alter_bit(altered_data,index)
        
    # If no error enforced, manually push one atleast
    if(altered_data==data):
        altered_data=alter_bit(altered_data,random.randint(1,(length-1)))
    
    # Return the altered bit string
    return altered_data


if __name__=='__main__':
    # Input data
    data=input('Input bit string to be altered : ')

    # Generate error
    print('Erroneous data : ',insert_error(data))