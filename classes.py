import msgpack # Install with: pip install msgpack
import socket
import random
import asyncio
import time
from encryption import *
from dotenv import load_dotenv
import os
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
RESET   = "\033[0m"
import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG)

class Connection:
    """Connection class that represents and is responsible for creating a connection with the server"""
    
    def __init__(self,ip,port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((ip, port))
        self.ip = ip
        self.port = port
        self.listening = True
        self.response = [0 for _ in range((37-22)+1)]
        self.session = None
        self.initiator = None
        self.on_message_received = None 
        
    def connect(self,incoming_data):
        data =  incoming_data
        #request handle is a random number
        data["request_handle"] = random.randint(0, 2**32 - 1)
        data = msgpack.packb(data)
        #ports 51820 & 51821 use encryption
        if self.port == 51820 or self.port == 51821:
            data = self.initiator.create_wireguard_transport_message(data)
        self.sock.send(data)
        data = self.sock.recv(1024)
        if self.port == 51820 or self.port == 51821:
            data = self.initiator.handle_wireguard_response(data)
        data = msgpack.unpackb(data)
        self.session = data["session"]
        return data  
    
    def getSession(self):
        return self.session
    
    async def send(self, data):
        """Send method adds the common parts of a message like the request handle and session number to every outgoing message."""
        if data["request_type"] != 1:
            data["session"] = self.session
        data["request_handle"] = random.randint(0, 2**32 - 1)
        new_data = msgpack.packb(data)
        if self.port == 51820 or self.port == 51821:
            new_data = self.initiator.create_wireguard_transport_message(new_data)
            
        logging.debug(f"{BLUE}{time.strftime('%X')} sending: {data}{RESET}")
        loop = asyncio.get_event_loop()
          
        await loop.run_in_executor(None, self.sock.send, new_data)
        
        await asyncio.sleep(2)
        info =self.response[data["request_type"]] 
        logging.debug(f"{time.strftime('%X')} response : {info}" )
        if data["request_type"] == 12:
            logging.debug(f"{time.strftime('%X')} special case response : {self.response[0]}" )
            return self.response[0]
        if self.response[data["request_type"]] == 0:
            return {}
        return self.response[data["request_type"]]
     
    async def send_wireguard(self, data):
        """Send message using the WireGuard protocol"""
        new_data = data if isinstance(data, bytes) else msgpack.packb(data)
        print(f"{BLUE}{time.strftime('%X')} sending: {data}{RESET}")
        self.sock.send(new_data)
        print("sent: ", new_data)
        
        # Enable response receiving
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(None, self.sock.recv, 1024)
        # Don't unpack if response is raw binary (WireGuard format)
        if response_data[:1] == b'\x02':  # WireGuard Message 2
            print(f"{time.strftime('%X')} response: {response_data}")
        else:
            response_data = msgpack.unpackb(response_data)
            print(f"{time.strftime('%X')} response: {response_data}")
        return response_data
        
        
    async def disconnect(self,data):
        """Disconnect method disconnects from the server and stops the listener thread for updates"""
        data = await self.send(data)
        if data["response_type"] == 23:
            
            print("listening set to false")
            self.listening = False
        print("not listening set to false")
        
        
        return data
    
    async def listen(self):
        """Listener method keeps listening thread active for server responses"""
        loop = asyncio.get_event_loop()
        while self.listening:
            try: 
                data = await loop.run_in_executor(None, self.sock.recv, 1024)
                if self.port == 51820 or self.port == 51821:
                    data = self.initiator.handle_wireguard_response(data)
                data = msgpack.unpackb(data)
                
                
                logging.debug(f"{GREEN}{time.strftime('%X')} Listener: {data}{RESET}")
                
                    
                self.response[data["response_type"]-21] = data
                
                if self.on_message_received:
                    self.on_message_received(data)
                else:
                    logging.debug(f"{RED} Listener callback not set {RESET}")
            except Exception as e:
                logging.debug(f"focus_input error: {e}") 
    
class User:
    """User class stores user information like name and a list of channels that the user has joined"""
    def __init__(self,name):
        self.username = name
        self.my_channels = []

class Manager:
    """Manager class manages the connection,sends messages and receives and processes responses"""
    def __init__(self):
        self.username = None
        self.channels = []
        self.connection = None
        self.on_message_received = None
        
    def setConnectionType(self,type):
        """setConnectionType creates a particular connection--either cleartext, encrypted or mac2(cookie)"""
        if type == "cleartext":
            self.connection = Connection('csc4026z.link',51825) 
        elif type=="encrypted":
            self.connection = Connection('csc4026z.link',51820)
        elif type == "cookie":
            self.connection = Connection('csc4026z.link', 51821)
        else:
            print("Error: invalid type")    
        
    def setUser(self,username):
        self.username = username

    def getUsername(self):
        return self.username 
       
    def send(self,data):
        return self.connection.send(data)
    def send_wireguard(self,data):
        return self.connection.send_wireguard(data)
      
    #! Channel Messages
    async def CHANNEL_CREATE(self,channel_name,description=""):
        """Create channel message"""
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

    """List available channels message"""
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
        
    async def CHANNEL_INFO(self,channel):
        """Message to get channel information"""
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

    async def CHANNEL_JOIN(self,channel):
        """Message to join channel"""
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
    
    async def CHANNEL_LEAVE(self,channel):
        """Message to leave channel"""
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

    async def CHANNEL_MESSAGE(self,channel,message):
        """Message to send a message to a channel"""
        data= {
            "request_type":9,               # request_type u8
            
            "channel":channel,
            "message":message
        } 
        data = await self.connection.send(data)
        if data == {}:
            logging.debug(f"repsonse to channel message not sent {data}")
            return
        response_type = data["response_type"]
        if response_type ==30:
            print(f"Message sent to channel \"{channel}\"")
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
    
    #! Session Messages
    def connect(self):
        """Message to connect to the server. Depending on the connection type, a specific handshake is initiated, or not in the case of cleartext"""
        print(self.connection.port)
        if self.connection.port == 51825:      
            data= {
                "request_type":1
            } 
            data = self.connection.connect(data)
            print(f"send protocol: {data}")
            response_type = data["response_type"]
            if response_type ==22:
                print(f"connected")
                self.username = data["username"]
                print(f"username set to {self.username}")
            else:
                error = data["error"]
                print(f"Error: \"{error}\"")
            logging.debug(data)    
            return data
        #encrypted connection
        elif self.connection.port == 51820:    
            #use static private key to initiate secure handshake with server 
            #load static private key from the .env file       
            load_dotenv()
            my_static_private = os.getenv('my_static_private')
            my_static_private = base64.b64decode(my_static_private) 
            my_static_public  = bytes(nacl.public.PrivateKey(my_static_private).public_key)

            print("my_static_private: ",my_static_private)
            print("my_static_public: ",my_static_public)
            self.connection.initiator  = Initiator(my_static_public,my_static_private)
            data = self.connection.initiator.new_handshake()
            print(f"data {data}")
            binary_msg = self.serialize_message_1(data)
            print(f"binray {binary_msg}")
            self.connection.sock.send(binary_msg)
            response = self.connection.sock.recv(1024)
            #response is b\0x2
            self.connection.initiator.process_response(response)      
            data= {
                "request_type":1
            } 
            data = self.connection.connect(data)
            print(f"send protocol: {data}")
            response_type = data["response_type"]
            if response_type ==22:
                print(f"connected")
                self.username = data["username"]
                print(f"username set to {self.username}")
            else:
                error = data["error"]
                print(f"Error: \"{error}\"")
            logging.debug(data)    
                
            return data
        
             #mac2 connection         
        elif self.connection.port == 51821:
            #use static private key to initiate secure handshake with server 
            #load static private key from the .env file 
            load_dotenv()
            my_static_private = os.getenv('my_static_private')
            my_static_private = base64.b64decode(my_static_private) #b'\x99x\x93eP\xdd\xb7h\xd5dJ\xc7\xa5~\x83\xbdX\x04M\xe29\x15\xe2\xf1\xe8\xd8VFk0\xf8\xa1'
            my_static_public  = bytes(nacl.public.PrivateKey(my_static_private).public_key)

            print("my_static_private: ",my_static_private)
            print("my_static_public: ",my_static_public)
            self.connection.initiator  = Initiator(my_static_public,my_static_private)
            data = self.connection.initiator.new_handshake()
            print(f"data {data}")
            binary_msg = self.serialize_message_1(data)
            print(f"binray {binary_msg}")
            self.connection.sock.send(binary_msg)
            response = self.connection.sock.recv(1024)
            #response is 0x3
                
            # decrypt cookie and generate the new handshake with calculated mac2
            new_handshake_data = self.connection.initiator.process_response_cookie(response)
            new_binary_msg = self.serialize_message_1(new_handshake_data)
                
            # send the second attempt
            self.connection.sock.send(new_binary_msg)
                
            # wait for the final 0x2 response
            final_response = self.connection.sock.recv(1024)
            if final_response[0:1] == b'\x02':
                self.connection.initiator.process_response(final_response)
                print("SECOND CALL OF PROCESS RESPONSE REACHED")
            else:
                print("Handshake failed after cookie submission.")
                return {}
                
            data= {
                "request_type":1
            } 
            print("ABOUT TO SEND DATA. IF NO RESPONSE, THREAD IS STUCK WAITING")
            data = self.connection.connect(data)
            print(f"send protocol: {data}")
            logging.debug(data)
            response_type = data["response_type"]
            if response_type ==22:
                print(f"connected")
                self.username = data["username"]
                print(f"username set to {self.username}")
            else:
                error = data["error"]
                print(f"Error: \"{error}\"")
            logging.debug(data)                   
            return data
        
    def serialize_message_1(self,msg_dict):
        """Construct message for secure handshake"""
        return (
            msg_dict["type"] +
            msg_dict["reserved"] +
            msg_dict["sender"].to_bytes(4, 'little') +
            msg_dict["ephemeral"] +
            msg_dict["static"] +
            msg_dict["timestamp"] +
            msg_dict["mac1"] +
            msg_dict["mac2"]
        )      
    
    async def ping(self):
        """Message to send pings/heartbeats to the server"""
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
        """Start loop for pinging the server and wait for username and channel list updates"""
        while self.connection.listening:
            await self.ping()
            await self.user_list_pro()
            await self.CHANNEL_LIST_PRO()
            await asyncio.sleep(30)
        print("pinging stopped")   
    
    async def disconnect(self):
        """Send message to disconnect from server"""
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
        print(f"{GREEN}listner started {RESET}")
        await self.connection.listen()
        print("listener closed")

#! User messages
    async def set_username(self,username):
        """Message to change username"""
        data= {
            "request_type":13,
            "username":username
        } 
        data = await self.connection.send(data)
        response_type = data["response_type"]
        if response_type ==34:
            print(f"set username")
            self.username = username
        else:
            error = data["error"]
            print(f"Error: \"{error}\"")
            
        return data
        
    async def user_list(self,channel=None,offset=None):
        """Message to return a list of active users"""
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
        """Message to send messages to another user (direct messages)"""
        try:
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
        except Exception as e:
                logging.debug(f"focus_input error: {e}")

    async def whoami(self):
        """Message to return the current username stored by the server"""
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
    
    async def whois(self,username):
        """Return information on another user"""
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
   
#class Message:
#    def __init__(self,data):
#        self.data = data
#    def encrypt(self):
#        pass
    

        

    
        