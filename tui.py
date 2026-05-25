from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll, VerticalScroll,Container
from textual.screen import Screen
from textual.widgets import Placeholder,Header,Footer
from textual.widget import Widget
from textual.reactive import reactive
from textual.widgets import Input,Button

import asyncio

import concurrent
import msgpack # Install with: pip install msgpack
import socket
import random
#from classes import connection
from classes import *
import sys
import os
from encryption import *
import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG,filemode='w')
    
user_types = ["Server","User","Channel"]
server_help_msg = "/disconnect | /username <name> | /whoami | /whois <user> | /userlist | /channels | /join <channel> | /leave <channel> | /create <channel> <description=optional>| /msg <user> <message> | /info <channel>|/msgChannel <channel> <message>"

class User(Widget):
    
    DEFAULT_CSS = """
    User {
        height: 7;
        border: round $primary;
        margin: 1;
        background: $panel;
        padding: 1;
    }
    """
    def __init__(self, label: str,type  :str = user_types[1]):
        super().__init__()
        self.label = label
        self.type = type
    
    def compose(self):
        yield Label(self.type+": "+self.label)
    async def on_click(self) -> None:
        self.app.active_chat =self.label
        chat = self.app.screen.query_one(ChatScreen)
        chat.clear_messages()
        chat.add_message("Current chat with",self.label)
        if self.label == "Server":
        #yield ChatMessage("Server",server_help_msg)
            
            chat.add_message("Help Menu",server_help_msg)
        if self.type == user_types[2]:
            await self.app.server.CHANNEL_JOIN(self.label)
            
            
            
            
    
class MyInput(Input):
    
    DEFAULT_CSS = """
    MyInput {
        width: 80%;
        height: 3;
    }
    """
    def compose(self):
        return super().compose()
    

class ChatList(VerticalScroll):
    DEFAULT_CSS = """
    ChatList {
        
        background: $boost;
    }
    """

    def compose(self) -> ComposeResult:
        yield User(label="Server",type=user_types[0])
        
    def add_user(self, username: str,type : str = user_types[1]) -> None:
        self.mount(User(label=username,type=type))
    def remove_user(self, username: str,type : str) -> None:
        for user in self.query(User):
            if user.label == username and user.type == type:
                user.remove()
        
            
            
class Name(Widget):
    """Generates a greeting."""

    who = reactive("name")

    def render(self) -> str:
        return f"Hello, {self.who}!"
    
    
class ChatMessageBar(Widget):
    DEFAULT_CSS = """
    ChatMessageBar {
        dock: bottom;
        height: 3;
    }
    """
    
    def compose(self):
        with HorizontalScroll():
            yield MyInput(placeholder="Enter message...")
            yield Button()
    async def on_button_pressed(self) -> None:
        await self._send()
    
    async def on_input_submitted(self) -> None:
        await self._send()
    
    async def _send(self) -> None:
        input_widget = self.query_one(MyInput)
        msg = input_widget.value.strip()
        logging.debug("msg: " , msg)
        
        input_widget.value = ""
        if msg:
            await self.handle_input(msg)
    
            
            
            
            
    async def handle_input(self, msg: str) -> None:
        chat = self.screen.query_one(ChatScreen)

        

        # Commands
        if msg.startswith("/"):
            await self.handle_command(msg, chat)
        else:
            # Regular channel message
            chat.add_message("Me", msg)
            #chat.add_message("test", self.app.active_chat)
            if self.app.active_chat != "Server":
               #chat.add_message("Me special", msg)
                if self.app.active_chat in self.app.user_list:
                    await self.app.server.user_message(self.app.active_chat, msg)
                if self.app.active_chat in self.app.channel_list:
                    await self.app.server.CHANNEL_MESSAGE(self.app.active_chat, msg)
            
            
            #chat.add_message(f"DM → {sub[0]}", sub[1])
                
            #await self.app.server.CHANNEL_MESSAGE(self.channel, msg)
    
    async def handle_command(self, msg: str, chat) -> None:
        parts = msg.split(" ", 1)
        cmd = parts[0].lower()

        match cmd:
            case "/disconnect":
                data = await self.app.server.disconnect()
                chat.add_message("System", data.get("message", "Disconnected"))
                self.app.exit()

            case "/username":
                if len(parts) > 1:
                    await self.app.server.set_username(parts[1])
                    chat.add_message("System", f"Username changed to {parts[1]}")
                else:
                    chat.add_message("System", "Usage: /username <name>")

            case "/whoami":
                data = await self.app.server.whoami()
                chat.add_message("System", str(data))

            case "/whois":
                if len(parts) > 1:
                    data = await self.app.server.whosis(parts[1])
                    chat.add_message("System", str(data))
                else:
                    chat.add_message("System", "Usage: /whois <username>")

            case "/userlist":
                data = await self.app.server.user_list_pro()
                chat.add_message("System", str(data))
                for u in data:
                    if u not in self.app.user_list:
                        self.screen.query_one(ChatList).add_user(u)
                        self.app.user_list += [u]

            case "/channels":
                data = await self.app.server.CHANNEL_LIST_PRO()
                chat.add_message("System", str(data))

            case "/join":
                if len(parts) > 1:
                    await self.app.server.CHANNEL_JOIN(parts[1])
                    self.channel = parts[1]
                    chat.add_message("System", f"Joined channel {parts[1]}")
                else:
                    chat.add_message("System", "Usage: /join <channel>")

            case "/leave":
                if len(parts) > 1:
                    await self.app.server.CHANNEL_LEAVE(parts[1])
                    chat.add_message("System", f"Left channel {parts[1]}")
                else:
                    chat.add_message("System", "Usage: /leave <channel>")

            case "/create":
                if len(parts) > 1:
                    sub = parts[1].split(" ", 1)
                    if len(sub) == 2:
                        
                        await self.app.server.CHANNEL_CREATE(sub[0],sub[1])
                        chat.add_message("System", f"Enter description for {parts[1]}:")
                    elif len(sub)==1:
                        await self.app.server.CHANNEL_CREATE(sub[0],"")
                        chat.add_message("System", f"Enter description for {parts[1]}:")
                        
                    else:
                        chat.add_message("System", "Usage: /create <channel>")
                else:
                    chat.add_message("System", "Usage: /create <channel>")

            case "/msg":
                if len(parts) > 1:
                    sub = parts[1].split(" ", 1)
                    if len(sub) == 2:
                        await self.app.server.user_message(sub[0], sub[1])
                        chat.add_message(f"DM → {sub[0]}", sub[1])
                    else:
                        chat.add_message("System", "Usage: /msg <username> <message>")
                else:
                    chat.add_message("System", "Usage: /msg <username> <message>")

            case "/info":
                if len(parts) > 1:
                    await self.app.server.CHANNEL_INFO(parts[1])
                else:
                    chat.add_message("System", "Usage: /info <channel>")
            case "/msgchannel":
                if len(parts) > 1:
                    sub = parts[1].split(" ", 1)
                    if len(sub) == 2:
                        await self.app.server.CHANNEL_MESSAGE(sub[0], sub[1])
                        chat.add_message(f"Channel → {sub[0]}", sub[1])
                    else:
                        chat.add_message("System", "Usage: /msg <username> <message>")
                else:
                    chat.add_message("System", "Usage: /msg <username> <message>")

            case "/help":
                chat.add_message("System",
                    server_help_msg
                )

            case _:
                chat.add_message("System", f"Unknown command: {cmd}. Type /help for commands.")
           

class ChatScreen(VerticalScroll):
    global active_chatScreen
    DEFAULT_CSS = """
    ChatMessages {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield ChatMessage("Current chat with","Server")
        yield ChatMessage("Help Menu",server_help_msg)
        #self.add_message("Server",server_help_msg)
        self.scroll_end()
    
    def add_message(self, username: str, message: str):
        self.mount(ChatMessage(username, message))
        self.scroll_end()  # scroll to latest msg
    def clear_messages(self) -> None:
        self.query(ChatMessage).remove()
        
 
        
        

    
        
        
        
class Chat(Container):
    DEFAULT_CSS = """
    Chat {
        width: 60%;
    }
    """


    
    def compose(self):
        yield ChatScreen()
        yield ChatMessageBar()       



class UserScreen(Screen):
    
    DEFAULT_CSS = """"""
    
    def compose(self) -> ComposeResult:
        yield Header(id="Header",show_clock=True)
        yield Footer(id="Footer")
        with HorizontalScroll():
            yield ChatList()
            yield Chat()
    
    def on_mount(self) -> None:
        for data in self.app.message_queue:
            chat = self.query_one(ChatScreen)
            username = data.get("username", "System")
            message = data.get("message", str(data))
            chat.add_message(username, message)
        self.app.message_queue.clear()
            
from textual.widgets import Label

class ChatMessage(Widget):
    DEFAULT_CSS = """
    ChatMessage {
        height: auto;
        padding: 1 2;
        margin: 0 1;
        background: $panel;
        border: round $primary;
        width: 100%;
    }
    ChatMessage.me {
        border: round green;
    }
    ChatMessage.system {
        border: round $warning;
    }
    Label {
        width: 100%;
    }
    """
    
    def __init__(self, username: str, message: str):
        super().__init__()
        self.username = username
        self.message = message
        
        if username == "Me":
            self.add_class("me")
        elif username == "System":
            self.add_class("system")
    
    def compose(self) -> ComposeResult:
        if self.username == "Me":
            yield Label(f"[bold green]{self.username}[/bold green]: {self.message}", markup=True)
        elif self.username == "System":
            yield Label(f"[bold yellow]{self.username}[/bold yellow]: {self.message}", markup=True)
        else:
            yield Label(f"[bold]{self.username}[/bold]: {self.message}", markup=True)



class ConnectionScreen(Screen):
    DEFAULT_CSS = """
    ConnectionScreen {
        align: center middle;
    }
    #options {
        width: 40;
        height: auto;
        padding: 2;
        background: $panel;
        border: round $primary;
    }
    Button {
        width: 100%;
        margin: 1 0;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(id="options"):
            yield Label("Welcome to NetSecChat", id="title")
            yield Button("Cleartext", id="cleartext")
            yield Button("Encrypted", id="encrypted")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cleartext":
            self.app.server.setConnectionType("cleartext")
        elif event.button.id == "encrypted":
            self.app.server.setConnectionType("encrypted")
        self.app.server.connect()
        self.app.server.connection.on_message_received = self.app.handle_incoming
        self.app.server.on_message_received = self.app.handle_incoming
        await self.app.push_screen(UserScreen())
        self.notify("Connected to server!")
        
       
        asyncio.create_task(self.app.server.start_ping_loop())
        asyncio.create_task(self.app.server.listen())
        
        
        
       
        
        


class LayoutApp(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),("q", "quit", "Close Everything"),("enter", "send", "Send message")]
  

    def __init__(self):
        super().__init__()
        self.server = Manager()
        self.message_queue = []
        self.channel_list = []
        self.user_list = []
        self.active_chat = "Server"
    
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
    
    def action_quit(self) -> None:
        # Cancel all background tasks
        
        self.exit()
    
    async def on_unmount(self) -> None:
        try:
            await self.server.disconnect()
            
        except:
            pass
        os._exit(0)  
        
    def on_ready(self) -> None:
        self.push_screen(ConnectionScreen())
    def handle_incoming(self, data: dict) -> None:
        #logging.debug(f"callback triggered, current screen: {self.screen.id}")
        self.call_later(self._update_ui, data)

    
    
    
    
    def _update_ui(self, data: dict) -> None:
        
        try:
            #logging.debug(f"Current screen: {self.screen}")
            #logging.debug(f"Screen id: {self.screen.id}")
            #logging.debug(f"All screens: {self.screen_stack}")
            #logging.debug(f"Screen children: {list(self.screen.query('*'))}")
            chat_screen = self.screen.query_one(ChatScreen)
            username = data.get("from_username") or data.get("channel") or "Server"
            
            
            logging.debug(data["response_type"])    
            message = data.get("message", str(data))
            if data["response_type"] == 24:
                message = "ping successful"
            if data["response_type"] == 35:
        
                for u in data["users"]:
                    if u not in self.app.user_list:
                        
                        self.screen.query_one(ChatList).add_user(u)
                        self.app.user_list += [u]
                        
                for u in self.app.user_list:
                    if u not in data["users"]:
                        
                        self.screen.query_one(ChatList).remove_user(u,user_types[1])
                        self.app.user_list.remove(u)
            if data["response_type"] == 26:
        
                for u in data["channels"]:
                    if u not in self.app.channel_list:
                        
                        self.screen.query_one(ChatList).add_user(u,type=user_types[2])
                        self.app.channel_list += [u]
                        
                for u in self.app.channel_list:
                    if u not in data["channels"]:
                        
                        self.screen.query_one(ChatList).remove_user(u,user_types[2])
                        self.app.channel_list.remove(u)
                    
                
            if data["response_type"] == 30 and  data["response_handle"] == None :
                
                if username == self.active_chat:
                    chat_screen.add_message(username, message)
            elif  data["response_type"] == 33 and  data["response_handle"] == None :
                if username == self.active_chat:
                    chat_screen.add_message(username, message)
                   
            else:
                        chat_screen.add_message(f"Not in current chat: {username}", message)
                
        except Exception as e:
            logging.debug(f"UI update error: {e}")

if __name__ == "__main__":
    app = LayoutApp()
    app.run()