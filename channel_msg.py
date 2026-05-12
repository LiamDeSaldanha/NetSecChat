import msgpack # Install with: pip install msgpack
import socket
import random
#from classes import connection
# = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.connect(('csc4026z.link', 51825))
#sock.send(msgpack.packb({'session': 1, 'request_type':3, 'request_handle': random.randint(0, 2**32 - 1)}))
#data, addr = sock.recvfrom(4096)
#print(msgpack.unpackb(data))

"""CHANNEL_CREATE """
def CHANNEL_CREATE(channel_name,description=""):
    data= {
        "request_type":4,
        "channel":channel_name,    
        "description":description      
    }
    
    data = connection.send(data)
    response_type = data["response_type"]
    
    if response_type ==25:
        channel = data["channel"]    # Name of new channel
        print(f"Channel \"{channel}\" created")
    else:
        error = data["error"]
        print(f"Error: \"{error}\"")
        return data
    
    return data

"""CHANNEL_LIST"""
def CHANNEL_LIST(offset=0):
    data= {
        "request_type":5,               # request_type u8
       
        "offset":offset
    }    
    data = connection.send(data)

    
    response_type = data["response_type"]
    
    if response_type ==26:
        channels = data["channels"]
        print(f"List \"{channels}\"")
    else:
        error = data["error"]
        print(f"Error: \"{error}\"")
        return data
    
    return data

"""CHANNEL_LIST_PRO"""
def CHANNEL_LIST_PRO(offset=0):  
    i =0
    data =CHANNEL_LIST(offset)
    channels = data["channels"]
    next_page = data["next_page"]
    if next_page:
        offset =10
        while next_page and i<10: # i is to limit incase recussion depth exceeded , can be removed if confident code works
            i+=1
            data =CHANNEL_LIST(offset)
            
            tmp_channels = data["channels"]
            next_page = data["next_page"]
            channels+=tmp_channels
            offset+=10

  
    return channels
    
"""CHANNEL_INFO"""
def CHANNEL_INFO(channel):
    data= {
        "request_type":6,               # request_type u8
       
        "channel":channel
    }
    data = connection.send(data)

    response_type = data["response_type"]
    if response_type==27:
        channel_name = data["channel"]
    
        description = data["description"]
        channel_members = data["members"]
        print(f"Channel name: \"{channel_name}\"\nDescription: {description}\nChannel members: {channel_members}")
    else:
        error = data["error"]
        print(f"Error: \"{error}\"")
    
    
    
    
    return channel_name,description,channel_members

"""CHANNEL_JOIN"""
def CHANNEL_JOIN(channel):
    data= {
        "request_type":7,               
        "channel":channel
    }
    data = connection.send(data)
    
    response_type = data["response_type"]
    if response_type ==28:
        
        print(f"Joined \"{channel}\"")
    else:
        
        error = data["error"]
        print(f"Error: \"{error}\"")
        
    
    
    
    
    
    return data
"""CHANNEL_LEAVE"""
def CHANNEL_LEAVE(channel):
    data= {
        "request_type":8,               # request_type u8
       
        "channel":channel
    }
    data = connection.send(data)
    
    
    response_type = data["response_type"]
    if response_type ==29:
        print(f"Left \"{channel}\"")
    else:
        error = data["error"]
        print(f"Error: \"{error}\"")
        

    return data

"""CHANNEL_MESSAGE"""
def CHANNEL_MESSAGE(channel,message):
    data= {
        "request_type":9,               # request_type u8
        
        "channel":channel,
        "message":message
    } 
    data = connection.send(data)
    response_type = data["response_type"]
    if response_type ==30:
        print(f"Message sent to channel \"{channel}\"")
    else:
        error = data["error"]
        print(f"Error: \"{error}\"")
        
    return data


    