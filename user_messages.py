import msgpack # Install with: pip install msgpack
import socket
import random

# = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.connect(('csc4026z.link', 51825))
#sock.send(msgpack.packb({'session': 1, 'request_type':3, 'request_handle': random.randint(0, 2**32 - 1)}))
#data, addr = sock.recvfrom(4096)
#print(msgpack.unpackb(data))

# This will return an error saying "Session not found", because you're not logged in yet. That confirms the server is active.

"""CONNECT_REQUEST"""
def CONNECT_REQUEST():
    return {
        'request_type' : 1, 
        'request_handle': random.randint(0, 2**32 - 1)
        }


"""CONNECT_RESPONSE-->REQUEST_TYPE = 24"""
def CONNECT_RESPONSE(data):
    session = data['session']
    welcome = data['message']
    username = data['username']
    return session, welcome, username

"""PING_REQUEST"""
def PING_REQUEST(session):
    return {
        'request_type':3,
        'session': session,
        'request_handle': random.randint(0, 2**32 - 1)

    }

"""PING_RESPONSE-->REQUEST_TYPE = 23"""
def PING_RESPONSE(data):
    session = data['session']
    #inlcude response handle?
    return data

"""DISCONNECT_REQUEST"""
def DISCONNECT_REQUEST(session):
    return {
        'request_type' : 2,
        'session' : session,
        'request_handle': random.randint(0, 2**32 - 1)
    }

"""DISCONNECT_RESPONSE-->REPONSE TYPE = 23"""
def DISCONNECT_RESPONSE(data):
    message = data['message']
    return message

"""oOK RESPONSE-->RESPONSE TYPE = 21"""
def OK_response():
     #will do this later. seems a bit redundant now because every request has a response
     return "OK from server"

"""ERROR_REPONSE-->RESPONSE TYPE = 20"""
def ERROR_response(data):
     error = data['error']
     return error

"""SERVER_RESPONSE-->RESPONSE TYPE = 36"""
def SERVER_message_RESPONSE(data):
     server_mssg = data['message']
     return server_mssg
     

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(('csc4026z.link', 51825))
    #very wonky but this is just to test
    keyboard = input(f"Welcome to a little test!\nOptions:\n1. CONNECT\n2. DISCONNECT\n")
    if keyboard == "1":
    #connect
        sock.send(msgpack.packb(CONNECT_REQUEST()))
        data, addr = sock.recvfrom(4096)
        data = msgpack.unpackb(data)
        session, welcome, username = CONNECT_RESPONSE(data)
        print(f"{welcome} IP address {addr[0]} at port number {addr[1]}\n Username is {username}")  
    keyboard = input(f"Welcome to a little test!\nOptions:\n1. CONNECT\n2. DISCONNECT\n")
    #while (keyboard != "2"):
    #     ajdka
         
    sock.send(msgpack.packb(DISCONNECT_REQUEST(session)))
    data, addr = sock.recvfrom(4096)
    data = msgpack.unpackb(data)
    goodbye = DISCONNECT_RESPONSE(data)
    print(f"{goodbye} from IP address {addr[0]} at port number {addr[1]}\n Username {username} is now terminated")  




if '__name__ == __main__':
    main()

 
    
