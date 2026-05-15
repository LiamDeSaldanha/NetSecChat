import msgpack # Install with: pip install msgpack
import socket
import random

# = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.connect(('csc4026z.link', 51825))
#sock.send(msgpack.packb({'': 1, 'request_type':3, 'request_handle': random.randint(0, 2**32 - 1)}))
#data, addr = sock.recvfrom(4096)
#print(msgpack.unpackb(data))

# This will return an error saying " not found", because you're not logged in yet. That confirms the server is active.



"""SET_USERNAME_RESPONSE"""
def SET_USERNAME_REQUEST( new_username):
    return {
        'request_type':  13,
        
        
        'username': new_username
    }

"""SET_USERNAME_RESPONSE--> REQUEST TYPE 34"""
def SET_USERNAME_RESPONSE(data):
    old_username = data['old_username']
    new_username = data['new_username']
    return old_username, new_username
    

"""USER_LIST_REQUEST"""
#separate message for listing users in a specific channel?
def USER_LIST():
    return {
        'request_type': 14,
        
        'request_handle': random.randint(0, 2**32 - 1)
    }

"""USER_LIST_RESPONSE"""
def USER_LIST_RESPONSE(data):
    users = data['users']
    next_page =  data['next_page']
    return users, next_page

"""WHOAMI_REQUEST"""
def WHOAMI_REQUEST():
    return {
        'request_type': 11,
        
        'request_handle': random.randint(0, 2**32 - 1)
    }

"""WHOAMI_RESPONSE-->REQUEST TYPE = 32"""
def WHOAMI_RESPONSE(data):
    username = data['username']
    return username

def WHOIS_REQUEST( username):
    return {
        'request_type': 10,
        
        
        'username': username
    }

"""WHOIS_RESPONSE-->REQUEST TYPE = 31"""
def WHOIS_RESPONSE(data):
    username = data['username']
    channels = data['channels']
    transport = data['transport']
    wireguard_PK = data['wireguard_public_key']
    return username, channels, transport, wireguard_PK



    

    
    







 
    
