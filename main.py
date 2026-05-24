import asyncio

import concurrent
import msgpack # Install with: pip install msgpack
import socket
import random
from channel_msg import *
from user_messages import *
from session_msg import *
#from classes import connection
from classes import *
import sys
import os
from encryption import *
#connection = Connection('csc4026z.link', 51825)    

server = Manager() 
 
async def main():
    typeOfConnection_text = f"Welcome to a little test!\nOptions:\n1. Cleartext\n2. Encrypted\n"
    menu_text = f"Welcome to a little test!\nOptions:\n1. CONNECT\n"
    type_of_conenction = input(typeOfConnection_text)
    
    if type_of_conenction =="1":
        server.setConnectionType("cleartext")
        
        
    elif type_of_conenction == "2":
        server.setConnectionType("encrypted")
        
        
        
        
    else:
        print("Invalid type")
    
        
    
    
    keyboard = input(menu_text)
    if keyboard == "1":
        
        server.connect()
        ping_task = asyncio.create_task(server.start_ping_loop())
        listen = asyncio.create_task(server.listen())
        handle_input = asyncio.create_task(handleInput())
        
        await asyncio.gather(listen, ping_task, handle_input, return_exceptions=True)
        
        
       
    else:
        print("Invalid input")
    
    

async def handleInput():
    
    
    loop_text = f"""Welcome to a little test!\n
2. DISCONNECT\n
3. CHANGE USERNAME\n
4. USER LIST\n
5. WHOAMI\n
6. WHOIS\n
7.CHANNEL_CREATE\n
8.CHANNEL_LIST\n
9.CHANNEL_INFO\n
10.CHANNEL_JOIN\n
11.CHANNEL_LEAVE\n
12.CHANNEL_MSG\n
13. User MSG\n
14. test\n
    """
    #very wonky but this is just to test
    loop = asyncio.get_event_loop()
    keyboard = await loop.run_in_executor(None, input, loop_text)
    
    while True:
        if keyboard =="2":
            data = await server.disconnect()
            goodbye = data["message"]
            print(f"{goodbye} from IP address {server.connection.ip} at port number {server.connection.port}\n Username {server.getUsername()} is now terminated")
            os._exit(0)
        
        if keyboard == "3":
            new_username = await loop.run_in_executor(None, input, "Enter you new username: ")
            
            #new_username = input(f"Enter you new username: ")
            
            data = await server.set_username(new_username)
            
            

        if keyboard == "4":
            channel = await loop.run_in_executor(None, input, "Filter by channel [Y\\N]?")
            #channel = input(f"Filter by channel [Y\\N]?")
            if channel == "N":
                data = await server.user_list_pro()
                
                
            elif channel =="Y":
                filter_channel = await loop.run_in_executor(None, input, "channel name:\n")
                
                #filter_channel = input("channel name:\n")
                data =await server.user_list_pro(filter_channel)
                
            else:
                print("Invalid input")
                
            

        if keyboard == "5":
            data = await server.whoami()
            
        if keyboard == '6':
            identity = await loop.run_in_executor(None, input, "It seems you're curious. Who are we spying on?\n")
            
            #identity = input (f"It seems you're curious. Who are we spying on?\n")
            data = await server.whosis(identity)
        
        if keyboard =="7":
            channel_name = await loop.run_in_executor(None, input, "Channel name:\n")
            description = await loop.run_in_executor(None, input, "Description:\n")
            
            #channel_name = input("Channel name:")
            #description = input("Description:")
            await server.CHANNEL_CREATE(channel_name,description)

        if keyboard =="8":
            
            print(await server.CHANNEL_LIST_PRO())

        if keyboard =="9":
            channel_name = await loop.run_in_executor(None, input, "Channel name:\n")
            
            #channel_name = input("Channel name:")
            await server.CHANNEL_INFO(channel_name)

        if keyboard =="10":
            channel_name = await loop.run_in_executor(None, input, "Channel name:\n")
            
            #channel_name = input("Channel name:")
            await server.CHANNEL_JOIN(channel_name)

        if keyboard =="11":
            channel_name = await loop.run_in_executor(None, input, "Channel name:\n")
            
            #channel_name = input("Channel name:")
            await server.CHANNEL_LEAVE(channel_name)

            #TODO
        if keyboard =="12":
            channel_name = await loop.run_in_executor(None, input, "Channel name:\n")
            msg = await loop.run_in_executor(None, input, "Message:\n")
            
            #channel_name = input("Channel name:")
            #msg = input("Message:")
            msg = Message(msg)
            msg = msg.data
            await server.CHANNEL_MESSAGE(channel_name,msg)
        
        
        if keyboard == "13":
            username = await loop.run_in_executor(None, input, "Send message to ?\n")
            msg = await loop.run_in_executor(None, input, "message?\n")
            
            
            #username = input("Send message to ?")
            #msg = input("message?")
            data = await server.user_message(username,msg)
            
        if keyboard == "14":
            intiator = Initiator(my_static_public,my_static_private)
            data = intiator.handshake_message()
            data = await server.send(data)
        keyboard = await loop.run_in_executor(None, input, loop_text)

        
            
  
    #goodbye = DISCONNECT_RESPONSE()
      




if __name__ == '__main__':
    asyncio.run(main())