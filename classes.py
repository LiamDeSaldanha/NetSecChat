import msgpack # Install with: pip install msgpack
import socket
import random
import asyncio
import time
#from channel_msg import *
from user_messages import *
from session_msg import *

RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
RESET   = "\033[0m"

#TODO
class Connection:
    
    def __init__(self,ip,port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((ip, port))
        self.ip = ip
        self.port = port
        self.listening = True
        self.response = [0 for _ in range((37-22)+1)]
        self.session = None
        
    def connect(self,incoming_data):
        data =  incoming_data
        data["request_handle"] = random.randint(0, 2**32 - 1)
        data = msgpack.packb(data)
        self.sock.send(data)
        data = self.sock.recv(4096)
        data = msgpack.unpackb(data)
        self.session = data["session"]
        return data  
    
    def getSession(self):
        return self.session
    
    async def send(self, data):
        if data["request_type"] != 1:
            data["session"] = self.session
        data["request_handle"] = random.randint(0, 2**32 - 1)
        new_data = msgpack.packb(data)
        print(f"{BLUE}{time.strftime('%X')} sending: {data}{RESET}")
        loop = asyncio.get_event_loop()
        
        #self.listening = False  # pause the listener
        
        await loop.run_in_executor(None, self.sock.send, new_data)
        #response = await loop.run_in_executor(None, self.sock.recv, 1024)
        
        #self.listening = True  # resume listener
        await asyncio.sleep(2)
        print(f"{time.strftime('%X')} response : ", self.response[data["request_type"]])
        if self.response[data["request_type"]] == 0:
            return {}
        return self.response[data["request_type"]]
    #TODO
    async def disconnect(self,data):
        data = await self.send(data)
        
        return data
    async def listen(self):
        loop = asyncio.get_event_loop()
        while self.listening:
            
            data = await loop.run_in_executor(None, self.sock.recv, 1024)
            data = msgpack.unpackb(data)
            print(f"{GREEN}{time.strftime('%X')} Listener: {data}{RESET}")
            if data["response_type"] == 23:
                self.listening = False
                
            self.response[data["response_type"]-21] = data
        
            
                
        
    
    
class User:
    def __init__(self,name):
        self.useranme = name
        self.my_channels = []
        pass
    def channel_msg(self):
        pass
    def dm(self):
        pass
    def getMyChannels(self):
        pass

class Manager:
    def __init__(self):
        self.username = None
        self.channels = []
        self.connection = None
        
    def setConnectionType(self,type):
        if type == "cleartext":
            self.connection = Connection('csc4026z.link',51825) 
        elif type=="encrypted":
            self.connection = Connection('csc4026z.link',51820)
        else:
            print("Error: invalid type")
        
        
    def setUser(self,username):
        self.useranme = username
    def getUsername(self):
        return self.useranme
    
       
    def send(self,data):
        return self.connection.send(data)
    
    
    
    #! Channel Messages
        """CHANNEL_CREATE """
    async def CHANNEL_CREATE(self,channel_name,description=""):
        data= {
            "request_type":4,
            "channel":channel_name,    
            "description":description      
        }
        
        data = await self.connection.send(data)
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
    async def CHANNEL_LIST(self,offset=0):
        data= {
            "request_type":5,               # request_type u8
            "offset":offset
        }    
        data = await self.connection.send(data)

        
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
    async def CHANNEL_LIST_PRO(self,offset=0):  
        i =0
        data =await self.CHANNEL_LIST(offset)
        channels = data["channels"]
        next_page = data["next_page"]
        if next_page:
            offset =10
            while next_page and i<10: # i is to limit incase recussion depth exceeded , can be removed if confident code works
                i+=1
                data =await self.CHANNEL_LIST(offset)
                
                tmp_channels = data["channels"]
                next_page = data["next_page"]
                channels+=tmp_channels
                offset+=10

    
        return channels
        
    """CHANNEL_INFO"""
    async def CHANNEL_INFO(self,channel):
        data= {
            "request_type":6,               # request_type u8
        
            "channel":channel
        }
        data = await self.connection.send(data)

        response_type = data["response_type"]
        if response_type==27:
            channel_name = data["channel"]
        
            description = data["description"]
            channel_members = data["members"]
            print(f"Channel name: \"{channel_name}\"\nDescription: {description}\nChannel members: {channel_members}")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        
        
        
        
        return data

    """CHANNEL_JOIN"""
    async def CHANNEL_JOIN(self,channel):
        data= {
            "request_type":7,               
            "channel":channel
        }
        data = await self.connection.send(data)
        
        response_type = data["response_type"]
        if response_type ==28:
            
            print(f"Joined \"{channel}\"")
        else:
            
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        
        
        
        
        
        return data
    """CHANNEL_LEAVE"""
    async def CHANNEL_LEAVE(self,channel):
        data= {
            "request_type":8,               # request_type u8
        
            "channel":channel
        }
        data = await self.connection.send(data)
        
        
        response_type = data["response_type"]
        if response_type ==29:
            print(f"Left \"{channel}\"")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            

        return data

    """CHANNEL_MESSAGE"""
    async def CHANNEL_MESSAGE(self,channel,message):
        data= {
            "request_type":9,               # request_type u8
            
            "channel":channel,
            "message":message
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==30:
            print(f"Message sent to channel \"{channel}\"")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    
    
    #! Session Messages
    def connect(self):
        data= {
            "request_type":1
        } 
        data = self.connection.connect(data)
        print(f"send protocol: {data}")
        response_type = data["response_type"]
        if response_type ==22:
            print(f"connected")
            self.useranme = data["username"]
            print(f"username set to {self.useranme}")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
        
        
    async def ping(self):
        data= {
            "request_type":3
            
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==24:
            print(f"{RED}ping succesful{RESET}")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    
    async def start_ping_loop(self):
        while self.connection.listening:
            await self.ping()
            await asyncio.sleep(30)
        print("pinging stopped")
    
    async def disconnect(self):
        data= {
            "request_type":2
        } 
        data = await self.connection.disconnect(data)
        print("test 1")
        response_type = data["response_type"]
        if response_type ==23:
            print(f"disconnected")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    
    #! Server unsolicted
    
    
    
    
    
    async def listen(self):
        print("listner started")
        await self.connection.listen()
        
     
     # Todo not needed    
        
        
    def error(self):
        pass
    def server_message(self):
        pass
    def server_shutdown(self):
        pass


#! User messages

    async def set_username(self,username):
        data= {
            "request_type":13,
            "username":username
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==34:
            print(f"set username")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
        
    async def user_list(self,channel=None,offset=None):
        data= {
            "request_type":14,
            
        } 
        if channel is not None:
            data["channel"] = channel
        if offset is not None:
            data["offset"]= offset
        
            
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==35:
            print(f"userlist")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    async def user_list_pro(self,channel=None,offset=None):  
        i =0
        data = await self.user_list(channel,offset)
        res= data["users"]
        next_page = data["next_page"]
        if next_page:
            offset =20
            while next_page and i<20: # i is to limit incase recussion depth exceeded , can be removed if confident code works
                i+=1
                data = await self.user_list(channel,offset)
                
                tmp_userlist = data["users"]
                next_page = data["next_page"]
                res+=tmp_userlist
                offset+=20

    
        return res
    async def user_message(self,to_user,message):
        
        data= {
            "request_type":12,
            "to_username":to_user,
            "message":message
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==21:
            print(f"OK recieved for message")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    async def whoami(self):
        data= {
            "request_type":11,
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==32:
            print(f"WhoamI complete")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    async def whosi(self,username):
        data= {
            "request_type":10,
            "username":username
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==31:
            print(f"set username")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data

    
class Message:
    def __init__(self,data):
        self.data = data
    def encrypt(self):
        pass
    

        

    
        