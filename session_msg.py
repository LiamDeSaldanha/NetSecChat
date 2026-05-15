import msgpack # Install with: pip install msgpack
import socket
import random

"""CONNECT_REQUEST"""
def CONNECT_REQUEST():
    return {
        'request_type' : 1, 
        
        }


"""CONNECT_RESPONSE-->REQUEST_TYPE = 24"""
def CONNECT_RESPONSE(data):
    session = data['session']
    welcome = data['message']
    username = data['username']
    return session, welcome, username

"""PING_REQUEST"""
def PING_REQUEST():
    return {
        'request_type':3,
        
        

    }

"""PING_RESPONSE-->REQUEST_TYPE = 23"""
def PING_RESPONSE(data):
    #inlcude response handle?
    return data

"""DISCONNECT_REQUEST"""
def DISCONNECT_REQUEST():
    return {
        'request_type' : 2
        
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