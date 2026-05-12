import msgpack # Install with: pip install msgpack
import socket
import random
#from channel_msg import *
from user_messages import *
from session_msg import *

#TODO
class Connection:
    def __init__(self,ip,port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((ip, port))
        self.ip = ip
        self.port = port
        
    def connect(self):
        
        data = self.send(CONNECT_REQUEST())
        self.session, welcome, username = CONNECT_RESPONSE(data)
        print(f"{welcome} IP address {self.ip} at port number {self.port}\n Username is {username}")
        return self.session, welcome, username  
    
    def getSession(self):
        return self.session
    
    def send(self,data):
        if data["request_type"] !=1:
            data["session"] = self.session
        data["request_handle"]=random.randint(0, 2**32 - 1)
        data = msgpack.packb(data)
        self.sock.send(data)
        data, addr = self.sock.recvfrom(4096)
        data = msgpack.unpackb(data)
        return data
    #TODO
    def disconnect(self):
        data = self.send(DISCONNECT_REQUEST())
        return data
    
    
    
class User:
    def __init__(self,name):
        self.useranme = name
        self.my_channels = []
        pass
    def channel_msg(self):
        pass
    def dm(self):
        pass
    def getMyChannels():
        pass

class Manager:
    def __init__(self,ip,port):
        self.user = None
        self.channels = []
        self.connection = Connection(ip,port)
        
    def addConnection(self,ip,port):
        self.connection = Connection(ip,port)
        
    def setUser(self,username):
        self.user = User(username)
    def getUsername(self):
        return self.user.useranme
    def connect(self):
        return self.connection.connect()
    def disconnect(self):
        return self.connection.disconnect()    
    def send(self,data):
        return self.connection.send(data)
    
        """CHANNEL_CREATE """
    def CHANNEL_CREATE(self,channel_name,description=""):
        data= {
            "request_type":4,
            "channel":channel_name,    
            "description":description      
        }
        
        data = self.connection.send(data)
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
    def CHANNEL_LIST(self,offset=0):
        data= {
            "request_type":5,               # request_type u8
            "offset":offset
        }    
        data = self.connection.send(data)

        
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
    def CHANNEL_LIST_PRO(self,offset=0):  
        i =0
        data =self.CHANNEL_LIST(offset)
        channels = data["channels"]
        next_page = data["next_page"]
        if next_page:
            offset =10
            while next_page and i<10: # i is to limit incase recussion depth exceeded , can be removed if confident code works
                i+=1
                data =self.CHANNEL_LIST(offset)
                
                tmp_channels = data["channels"]
                next_page = data["next_page"]
                channels+=tmp_channels
                offset+=10

    
        return channels
        
    """CHANNEL_INFO"""
    def CHANNEL_INFO(self,channel):
        data= {
            "request_type":6,               # request_type u8
        
            "channel":channel
        }
        data = self.connection.send(data)

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
    def CHANNEL_JOIN(self,channel):
        data= {
            "request_type":7,               
            "channel":channel
        }
        data = self.connection.send(data)
        
        response_type = data["response_type"]
        if response_type ==28:
            
            print(f"Joined \"{channel}\"")
        else:
            
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        
        
        
        
        
        return data
    """CHANNEL_LEAVE"""
    def CHANNEL_LEAVE(self,channel):
        data= {
            "request_type":8,               # request_type u8
        
            "channel":channel
        }
        data = self.connection.send(data)
        
        
        response_type = data["response_type"]
        if response_type ==29:
            print(f"Left \"{channel}\"")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            

        return data

    """CHANNEL_MESSAGE"""
    def CHANNEL_MESSAGE(self,channel,message):
        data= {
            "request_type":9,               # request_type u8
            
            "channel":channel,
            "message":message
        } 
        data = self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==30:
            print(f"Message sent to channel \"{channel}\"")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data

    
    

    
    

    
    
class Message:
    def __init__(self,data):
        self.data = data
    def encrypt(self):
        pass
    

        

    
        