from typing import Text

from textual.app import App, ComposeResult
from textual.containers import HorizontalScroll, VerticalScroll, Container, Horizontal
from textual.screen import Screen, ModalScreen
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


####### AI Declaration ##################
# Ai was used for most of the CSS
# AI was used to debug textual errors such as screens not being found and specific methods not existing for soem protocols lile label for a input


class ChannelButton(Button):
    DEFAULT_CSS = """
    ChannelButton {
        width: 100%;
        height: auto;
        background: $primary;
        color: $text;
        border: none;
        text-style: bold;
        margin-top: 1;
    }

   

    

    ChannelButton.-joined {
        background: $error;
    }

    ChannelButton.-joined:hover {
        background: $error-lighten-2;
    }
    """
   
    def __init__(self, user_name: str, user_type: str):
        super().__init__(label="Join")  
        self.joined = False
        self.user_name = user_name
        self.user_type = user_type
        
        if user_name in self.app.my_created_channels:
            self.label = "Leave"
            self.joined = True
            self.add_class("-joined")
            
         
    
    
    async def on_click(self,event) -> None:
   
        
        try:   
            if self.user_type == user_types[2]:
                
                if not self.joined:
                    data = await self.app.server.CHANNEL_JOIN(self.user_name)
                   # if data["response_type"] ==20 and data["error"] == 'Already in channel':
                    #    pass
                    self.label = Text("Leave")
                    
                    self.joined = True
                    self.add_class("-joined")   
                    
                else:
                    await self.app.server.CHANNEL_LEAVE(self.user_name)
                    await self.app.server.CHANNEL_LIST_PRO()
                    
                    self.label = Text("Join")
                    self.joined = False
                    self.remove_class("-joined")
               
                        
        except Exception as e:
            logging.debug(f"UI update error: {e}")

class InfoChannelButon(Button):
    DEFAULT_CSS = """
    InfoChannelButon {
        width: 100%;
       
        background: $primary;
        color: $text;
        border: none;
        text-style: bold;
        margin-top: 1;
    }

    """
   
    def __init__(self, user_name: str):
        super().__init__(label="Info")  
        self.user_name = user_name
    
    async def on_click(self,event) -> None:
   
        try:
            data = await self.app.server.CHANNEL_INFO(self.user_name)
            if data["response_type"] != 20:

                description = "description: " +data["description"]+"\n"
                members = "members: " + ", ".join(data["members"]) + "\n"
                channel ="channel name: " + data["channel"]+"\n"
                
                self.app.push_screen(ChannelInfoModal(
                                    f"Channel Info",
                                    channel+description+members,
                                    "",
                                    user_types[2]
                                ))
        except Exception as e:
            logging.debug(f"UI update error: {e}") 
                   
               
                        
        

class UnreadDot(Widget):
    DEFAULT_CSS = """
    UnreadDot {
        width: 1;
        height: 1;
        margin-left: 1;
        background: white;
        border: round white;
    }
    UnreadDot.-hidden {
        display: none;
    }
    """


class User(Widget):
    
    DEFAULT_CSS = """
    User {
        height: auto;
        border: round $primary;
        margin: 1;
        background: $panel;
        padding: 1;
    }
    User > Horizontal {
        height: 1;
    }
    User Label {
        height: 1;
    }
    """
    unread = reactive(False)

    def __init__(self, label: str,type  :str = user_types[1]):
        super().__init__()
        self.label = label
        self.type = type
        
    
    def compose(self):
        with Horizontal():
            yield Label(self.type+": "+self.label)
            yield UnreadDot()
        if self.type == "Channel":
            yield ChannelButton(user_name=self.label, user_type=self.type)
            yield InfoChannelButon(user_name=self.label)

    def on_mount(self) -> None:
        self._sync_unread()

    def watch_unread(self, value: bool) -> None:
        self._sync_unread()

    def set_unread(self, value: bool) -> None:
        self.unread = value

    def _sync_unread(self) -> None:
        try:
            dot = self.query_one(UnreadDot)
            if self.unread:
                dot.remove_class("-hidden")
            else:
                dot.add_class("-hidden")
        except Exception as e:
            logging.debug(f"UI update error: {e}")
    
    async def on_click(self, event) -> None:
        try:
            if isinstance(event.control, (ChannelButton, InfoChannelButon)):
                return
            self.set_unread(False)
            self.app.active_chat =self.label
            chat = self.app.screen.query_one(ChatScreen)
            chat.clear_messages()
            chat.add_message("Current chat with",self.label)
            if self.label == "Server":
       
            
                chat.add_message("Help Menu",server_help_msg)
        
        
           
            if self.type == user_types[2]:
                
                
                history = self.app.channel_list.get(self.label, [])
                
                for username, message in history:
                    chat.add_message(username, message)
                
                
            if self.type == user_types[1]:  
                
            
                history = self.app.user_list.get(self.label, [])

                for username, message in history:
                    if username =="Me":
                        
                        chat.add_message(username, message)
                    else:
                        chat.add_message(username, message)
                
                        
                        
        except Exception as e:
            logging.debug(f"UI update error: {e}")
            
            
            
            
            
    
class MyInput(Input):
    
    DEFAULT_CSS = """
    MyInput {
        width: 1fr;
        height: 3;
    }
    """
    def compose(self):
        return super().compose()

class RefreshButton(Button):
    DEFAULT_CSS = """
    RefreshButton {
        width: 1fr;
    }
    """
    def __init__(self):
        super().__init__(label = "Refresh")
    async def _on_click(self, event):
        
        await self.app.server.user_list_pro()
        await asyncio.sleep(1)
        await self.app.server.CHANNEL_LIST_PRO()
        
        
        
class DisconnectButton(Button):
    DEFAULT_CSS = """
    DisconnectButton {
        width: 1fr;
    }
    """
    def __init__(self):
        super().__init__(label = "Disconnect")
        
    def _on_click(self, event):
        self.app.action_quit();
        
class ChangeUsernameButton(Button):
    DEFAULT_CSS = """
    ChangeUsernameButton {
        width: 1fr;
    }
    """
    def __init__(self):
        super().__init__(label = "Change username")
        
    def _on_click(self, event):
        self.app.push_screen(UsernameModal(
                            "",
                            "Change Username",
                            "",
                            user_types[1]
                        ))


class CreateChannelButton(Button):
    DEFAULT_CSS = """
    CreateChannelButton {
        width: 1fr;
    }
    """
    def __init__(self):
        super().__init__(label = "Create Channel")
        
    def _on_click(self, event):
        self.app.push_screen(CreateChannelModal(
                            "",
                            "Channel created",
                            "",
                            user_types[1]
                        ))     
        
class SettingPanel(Widget):
    DEFAULT_CSS = """
    SettingPanel {
        dock: bottom;
        height: auto;
        align: center middle;
        background: $boost;
    }
    """
    
    def compose(self):
        
        yield RefreshButton()  
        yield ChangeUsernameButton()
        yield CreateChannelButton()
        
        yield DisconnectButton()

class ChatList(VerticalScroll):
    DEFAULT_CSS = """
    ChatList {
        background: $boost;
        height: 1fr;
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

    def mark_unread(self, username: str, type: str, value: bool) -> None:
        for user in self.query(User):
            if user.label == username and user.type == type:
                user.set_unread(value)
                return
        
            

    
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
            yield Button(label="Send")
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

    def _format_list(self, title: str, items: list) -> str:
        if not items:
            return f"{title}: (none)"
        return f"{title} ({len(items)}): " + ", ".join(str(i) for i in items)

    def _format_payload(self, data: dict, default_message: str = "OK") -> str:
        if not isinstance(data, dict):
            return str(data)
        if data.get("error"):
            return f"Error: {data['error']}"

        hidden_keys = {
            "response_type",
            "request_type",
            "request_handle",
            "response_handle",
            "session",
        }
        payload = {k: v for k, v in data.items() if k not in hidden_keys}
        if not payload:
            return default_message

        lines = []
        for key, value in payload.items():
            if isinstance(value, list):
                value = ", ".join(str(i) for i in value) if value else "(none)"
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
            
            
            
            
    async def handle_input(self, msg: str) -> None:
        chat = self.screen.query_one(ChatScreen)

        if self.app.pending_channel_name:
            channel_name = self.app.pending_channel_name
            self.app.pending_channel_name = None
            await self.app.server.CHANNEL_CREATE(channel_name, msg)
            chat.add_message("Server", f"Channel {channel_name} created")
            return
        

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
                    self.app.user_list[self.app.active_chat].append(("Me", msg))
                    
                if self.app.active_chat in self.app.channel_list:
                    await self.app.server.CHANNEL_MESSAGE(self.app.active_chat, msg)
                    self.app.channel_list[self.app.active_chat].append(("Me", msg))
                    
            
            
            #chat.add_message(f"DM → {sub[0]}", sub[1])
                
            #await self.app.server.CHANNEL_MESSAGE(self.channel, msg)
    
    async def handle_command(self, msg: str, chat) -> None:
        parts = msg.split(" ", 1)
        cmd = parts[0].lower()

        match cmd:
            case "/disconnect":
                #data = await self.app.server.disconnect()
                #chat.add_message("Server", data.get("message", "Disconnected"))
                self.app.action_quit();

            case "/username":
                if len(parts) > 1:
                    new_username = parts[1]
                    current_username = self.app.server.getUsername()
                    if new_username == current_username:
                        chat.add_message("Server", "Error: new username matches current username")
                    else:
                        await self.app.server.set_username(new_username)
                        chat.add_message("Server", f"Username changed to {new_username}")
                        self.app.sub_title = new_username
                else:
                    chat.add_message("Server", "Usage: /username <name>")

            case "/whoami":
                data = await self.app.server.whoami()
                chat.add_message("Server", self._format_payload(data, "Whoami complete"))

            case "/whois":
                if len(parts) > 1:
                    data = await self.app.server.whois(parts[1])
                    chat.add_message("Server", self._format_payload(data, "Whois complete"))
                else:
                    chat.add_message("Server", "Usage: /whois <username>")

            case "/userlist":
                data = await self.app.server.user_list_pro()
                chat.add_message("Server", self._format_list("Users", data))
                current_username = self.app.server.getUsername()
                for u in data:
                    if u == current_username:
                        continue
                    if u not in self.app.user_list:
                        self.screen.query_one(ChatList).add_user(u)
                        self.app.user_list += [u]
                #if current_username in self.app.user_list:
                #    self.screen.query_one(ChatList).remove_user(current_username, user_types[1])
                #    self.app.user_list.remove(current_username)

            case "/channels":
                data = await self.app.server.CHANNEL_LIST_PRO()
                chat.add_message("Server", self._format_list("Channels", data))

            case "/join":
                if len(parts) > 1:
                    await self.app.server.CHANNEL_JOIN(parts[1])
                    self.channel = parts[1]
                    chat.add_message("Server", f"Joined channel {parts[1]}")
                else:
                    chat.add_message("Server", "Usage: /join <channel>")

            case "/leave":
                if len(parts) > 1:
                    self.app.server.CHANNEL_LEAVE(parts[1])
                    chat.add_message("Server", f"Left channel {parts[1]}")
                    
                else:
                    chat.add_message("Server", "Usage: /leave <channel>")

            case "/create":
                if len(parts) > 1:
                    sub = parts[1].split(" ", 1)
                    if len(sub) == 2:
                        
                        await self.app.server.CHANNEL_CREATE(sub[0],sub[1])
                        self.app.my_created_channels.append(sub[0])
                        chat.add_message("Server", f"Channel {sub[0]} created")
                    elif len(sub)==1:
                        self.app.pending_channel_name = sub[0]
                        chat.add_message("Server", f"Enter description for {sub[0]}:")
                        self.app.my_created_channels.append(sub[0])
                    else:
                        chat.add_message("Server", "Usage: /create <channel>")
                else:
                    chat.add_message("Server", "Usage: /create <channel>")

            case "/msg":
                if len(parts) > 1:
                    sub = parts[1].split(" ", 1)
                    if len(sub) == 2:
                        await self.app.server.user_message(sub[0], sub[1])
                        chat.add_message(f"DM → {sub[0]}", sub[1])
                    else:
                        chat.add_message("Server", "Usage: /msg <username> <message>")
                else:
                    chat.add_message("Server", "Usage: /msg <username> <message>")

            case "/info":
                if len(parts) > 1:
                    data = await self.app.server.CHANNEL_INFO(parts[1])
                    chat.add_message("Server", self._format_payload(data, "Channel info"))
                else:
                    chat.add_message("Server", "Usage: /info <channel>")
            case "/msgchannel":
                if len(parts) > 1:
                    sub = parts[1].split(" ", 1)
                    if len(sub) == 2:
                        await self.app.server.CHANNEL_MESSAGE(sub[0], sub[1])
                        chat.add_message(f"Channel → {sub[0]}", sub[1])
                    else:
                        chat.add_message("Server", "Usage: /msg <username> <message>")
                else:
                    chat.add_message("Server", "Usage: /msg <username> <message>")

            case "/help":
                chat.add_message("Server",
                    server_help_msg
                )

            case _:
                chat.add_message("Server", f"Unknown command: {cmd}. Type /help for commands.")
           

class ChatScreen(VerticalScroll):
    global active_chatScreen
    DEFAULT_CSS = """
    ChatScreen {
        height: 1fr;
        background: $boost;
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

class Chat2(Container):
    DEFAULT_CSS = """
    Chat2 {
        height: 100%;
    }
    """
    


    
    def compose(self):
        yield ChatList()
        yield SettingPanel()  





class UserScreen(Screen):
    
    
    
    def compose(self) -> ComposeResult:
        yield Header(id="Header",show_clock=True)
        yield Footer(id="Footer")
        with HorizontalScroll():
            yield Chat2()
            yield Chat()
    
    def on_mount(self) -> None:
        
        for data in self.app.message_queue:
            chat = self.query_one(ChatScreen)
            username = data.get("username", "Server")
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
    ChatMessage.server {
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
        elif username == "Server":
            self.add_class("server")
        
    
    def compose(self) -> ComposeResult:
        if self.username == "Me":
            yield Label(f"[bold green]{self.username}[/bold green]: {self.message}", markup=True)
        elif self.username == "Server":
            yield Label(f"[bold yellow]{self.username}[/bold yellow]: {self.message}", markup=True)
        else:
            yield Label(f"[bold]{self.username}[/bold]: {self.message}", markup=True)


#AI used to help make the notification modal screen
class NotificationModal(ModalScreen):
    DEFAULT_CSS = """
    NotificationModal {
        align: center middle;
    }
    #modal {
        width: 60;
        height: auto;
        padding: 1;
        background: $panel;
        border: round $warning;
    }
    #modal_buttons {
        height: auto;
    }
    #modal_buttons Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(self, title: str, body: str, chat_name: str, chat_type: str):
        super().__init__()
        self.title = title
        self.body = body
        self.chat_name = chat_name
        self.chat_type = chat_type

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label(f"[bold]{self.title}[/bold]", markup=True)
            yield Label(self.body)
            with Container(id="modal_buttons"):
                yield Button("Jump to chat", id="jump")
                yield Button("OK", id="ok")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.app.pop_screen()
        elif event.button.id == "jump":
            self.app.pop_screen()
            await self.app.open_chat(self.chat_name, self.chat_type)
            
            
            
#Adapted NotificationModal
class UsernameModal(ModalScreen):
    DEFAULT_CSS = """
    UsernameModal {
        align: center middle;
    }
    #modal {
        width: 60;
        height: auto;
        padding: 1;
        background: $panel;
        border: round $warning;
    }
    #modal_buttons {
        height: auto;
    }
    #modal_buttons Button {
        width: 100%;
        margin-top: 1;
    }
    #cancel {
        color: $error;
    }
    """

    def __init__(self, title: str, body: str, chat_name: str, chat_type: str):
        super().__init__()
        self.title = title
        self.body = body
        self.chat_name = chat_name
        self.chat_type = chat_type

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label(f"[bold]{self.title}[/bold]", markup=True)
            yield Label(self.body)
            with Container(id="modal_buttons"):
                yield MyInput(placeholder="Enter new username", id="input")
                yield Button("Confirm", id="ok")
                yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            input_widget = self.query_one(MyInput)
            new_username = input_widget.value.strip()

            chat_screen = None
            for screen in self.app.screen_stack:
                if isinstance(screen, UserScreen):
                    chat_screen = screen.query_one(ChatScreen)
                    break

            if not new_username:
                if chat_screen:
                    chat_screen.add_message("Server", "Error: username required")
                return

            current_username = self.app.server.getUsername()
            if new_username == current_username:
                if chat_screen:
                    chat_screen.add_message(
                        "Server", "Error: new username matches current username"
                    )
                return

            data = await self.app.server.set_username(new_username)
            if data.get("error"):
                if chat_screen:
                    chat_screen.add_message("Server", f"Error: {data['error']}")
                return

            self.app.sub_title = new_username
            if chat_screen:
                chat_screen.add_message("Server", f"Username changed to {new_username}")
            self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()
            
class CreateChannelModal(ModalScreen):
    DEFAULT_CSS = """
    CreateChannelModal {
        align: center middle;
    }
    #modal {
        width: 60;
        height: auto;
        padding: 2;
        background: $panel;
        border: round $warning;
    }
    #modal_buttons {
        height: auto;
    }
    #modal_buttons Button {
        width: 100%;
        margin-top: 1;
    }
    #cancel {
        color: $error;
    }
    """

    def __init__(self, title: str, body: str, chat_name: str, chat_type: str):
        super().__init__()
        self.title = title
        self.body = body
        self.chat_name = chat_name
        self.chat_type = chat_type

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label(f"[bold]{self.title}[/bold]", markup=True)
            yield Label(self.body)
            with Container(id="modal_buttons"):
                yield MyInput(placeholder="Enter channel name", id="input1")
                yield MyInput(placeholder="Enter description", id="input2")
                yield Button("Confirm", id="ok")
                yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            channel_name = self.query_one("#input1").value.strip()
            description = self.query_one("#input2").value.strip()

            chat_screen = None
            for screen in self.app.screen_stack:
                if isinstance(screen, UserScreen):
                    chat_screen = screen.query_one(ChatScreen)
                    break

            if not channel_name:
                if chat_screen:
                    chat_screen.add_message("Server", "Error: channel name required")
                return

            data = await self.app.server.CHANNEL_CREATE(channel_name, description)
            if data.get("error"):
                if chat_screen:
                    chat_screen.add_message("Server", f"Error: {data['error']}")
                return

            self.app.my_created_channels.append(channel_name)
            if chat_screen:
                chat_screen.add_message("Server", f"Channel {channel_name} created")
            self.app.pop_screen()
        elif event.button.id == "cancel":
            self.app.pop_screen()

#Adapted NotificationModal
class ChannelInfoModal(ModalScreen):
    DEFAULT_CSS = """
    ChannelInfoModal {
        align: center middle;
    }
    #modal {
        width: 60;
        height: auto;
        padding: 2;
        background: $panel;
        border: round $warning;
    }
    #modal_buttons {
        height: auto;
    }
    #modal_buttons Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(self, title: str, body: str, chat_name: str, chat_type: str):
        super().__init__()
        self.title = title
        self.body = body
        self.chat_name = chat_name
        self.chat_type = chat_type

    def compose(self) -> ComposeResult:
        with Container(id="modal"):
            yield Label(f"[bold]{self.title}[/bold]", markup=True)
            yield Label(self.body)
            with Container(id="modal_buttons"):
                yield Button("OK", id="ok")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.app.pop_screen()
            
            

        

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
            yield Button("Cookie(Mac2)", id = "cookie")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        port = 0
        if event.button.id == "cleartext":
            self.app.server.setConnectionType("cleartext")
            port = 51825
        elif event.button.id == "encrypted":
            self.app.server.setConnectionType("encrypted")
            port = 51820
        elif event.button.id == "cookie":
            self.app.server.setConnectionType("cookie")
            port = 51821
        data =  self.app.server.connect()

        
        self.app.server.connection.on_message_received = self.app.handle_incoming
        self.app.server.on_message_received = self.app.handle_incoming
        await self.app.push_screen(UserScreen())
        self.app.sub_title = data["username"]
        self.notify(f"Connected to server on port {port}!")
        
       
        asyncio.create_task(self.app.server.start_ping_loop())
        asyncio.create_task(self.app.server.listen())
        
        
        
       
        
        


class LayoutApp(App):
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),("q", "quit", "Close Everything"),("enter", "send", "Send message")]
  

    def __init__(self):
        super().__init__()
        self.server = Manager()
        self.my_created_channels = []
        self.message_queue = []
        self.channel_list = {}
        self.user_list = {}
        self.server_messages = {}
        self.active_chat = "Server"
        self.pending_channel_name = None
        self.username=""
    
    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
    
    def action_quit(self) -> None:
        # Cancel all background tasks
        
        self.exit()
    
    def on_mount(self) -> None:
        self.title = "Your username"
        self.sub_title = self.username
    
    async def on_unmount(self) -> None:
        try:
            await self.server.disconnect()
            
        except:
            pass
        os._exit(0)  
        
    def on_ready(self) -> None:
        self.push_screen(ConnectionScreen())

    async def open_chat(self, chat_name: str, chat_type: str) -> None: #! broken
        self.active_chat = chat_name
        self.screen.query_one(ChatList).mark_unread(chat_name, chat_type, False)
        chat = self.screen.query_one(ChatScreen)
        chat.clear_messages()
        chat.add_message("Current chat with", chat_name)
        if chat_name == "Server":
            chat.add_message("Help Menu", server_help_msg)
            return

        try:
            if chat_type == user_types[2]:
                await self.server.CHANNEL_JOIN(chat_name)
                history = self.channel_list.get(chat_name, [])
            elif chat_type == user_types[1]:
                history = self.user_list.get(chat_name, [])
            else:
                history = []

            for username, message in history:
                chat.add_message(username, message)
        except Exception as e:
            logging.debug(f"UI update error: {e}")
    def handle_incoming(self, data: dict) -> None:
        #logging.debug(f"callback triggered, current screen: {self.screen.id}")
        self.call_later(self._update_ui, data)

    
    
    
    
    def _update_ui(self, data: dict) -> None:
        
        try:
            for screen in self.screen_stack:
                if isinstance(screen, UserScreen):
                    chat_screen = screen.query_one(ChatScreen)
                    break
            #logging.debug(f"Current screen: {self.screen}")
            #logging.debug(f"Screen id: {self.screen.id}")
            #logging.debug(f"All screens: {self.screen_stack}")
            #logging.debug(f"Screen children: {list(self.screen.query('*'))}")
            chat_screen = self.screen.query_one(ChatScreen)
            username = data.get("from_username")  or data.get("channel") or "Server"
            #if username == "channel":
            #if username =="Server":
                   
            
            
            logging.debug(data["response_type"])    
            message = data.get("message", str(data))
            if data["response_type"] == 24:
                # Skip UI updates for ping responses.
                return
            if data["response_type"] == 35:
                current_username = self.app.server.getUsername()
                for u in data["users"]:
                    if u == current_username:
                        continue
                    if u not in self.app.user_list.copy().keys():
                        
                        self.screen.query_one(ChatList).add_user(u)
                        self.app.user_list[u] = []
                    #self.app.user_list[username].append((username, message))
                        
                for u in self.app.user_list.copy().keys():
                    if u not in data["users"] and not  len(self.app.user_list.copy().keys())>=10:
                        
                        self.screen.query_one(ChatList).remove_user(u,user_types[1])
                        del self.app.user_list[u]
                if current_username in self.app.user_list:
                    self.screen.query_one(ChatList).remove_user(current_username, user_types[1])
                    del self.app.user_list[current_username]
                # Skip UI message updates for user list responses.
                return
                
            if data["response_type"] == 26:
        
                for u in data["channels"]:
                    if u not in self.app.channel_list.copy().keys():
                        
                        self.screen.query_one(ChatList).add_user(u,type=user_types[2])
                        self.app.channel_list[u] = []
                    #self.app.channel_list[u].append((username, message))
                        
                for u in self.app.channel_list.copy().keys():
                    if u not in data["channels"] and not len(self.app.channel_list.copy().keys())>=10 :
                        
                        self.screen.query_one(ChatList).remove_user(u,user_types[2])
                        del self.app.channel_list[u]
                # Skip UI message updates for channel list responses.
                return
                    
                
            if data["response_type"] == 30   :
                if data["response_handle"] is None:
                    channel_user_name = data.get("username")
                    if username not in self.app.channel_list:
                        self.app.channel_list[username] = []
                    self.app.channel_list[username].append((channel_user_name, message))
                    if username == self.active_chat:
                        chat_screen.add_message(channel_user_name, message)
                        logging.debug(f"Channel list {self.app.channel_list}")
                        logging.debug(f"User list {self.app.user_list}")
                    else:
                        self.screen.query_one(ChatList).mark_unread(
                            username, user_types[2], True
                        )
                        self.push_screen(NotificationModal(
                            f"Channel message: {username}",
                            f"{channel_user_name}: {message}",
                            username,
                            user_types[2]
                        ))

                    
                    
            elif  data["response_type"] == 33  :
                if data["response_handle"] is None:
                    if username not in self.app.user_list:
                        self.app.user_list[username] = []
                    self.app.user_list[username].append((username, message))
                    if username == self.active_chat:
                        chat_screen.add_message(username, message)
                        logging.debug(self.app.user_list)
                    else:
                        self.screen.query_one(ChatList).mark_unread(
                            username, user_types[1], True
                        )
                        self.push_screen(NotificationModal(
                            f"New message from {username}",
                            message,
                            username,
                            user_types[1]
                        ))
                   
            else:
                
                    
                if data["response_type"]== 28:
                    message = data["username"] + " joined channel"
                    if username == self.active_chat:
                        chat_screen.add_message("Channel: ", message)
                    self.app.channel_list[username].append(("Channel: ", message))
                    
                elif data["response_type"]== 29:
                    message = data["username"] + " left channel"
                    if username == self.active_chat:
                        chat_screen.add_message("Channel: ", message)
                    self.app.channel_list[username].append(("Channel: ", message))
                elif data["response_type"]== 36:
                    if  self.active_chat == "Server":
                        chat_screen.add_message("Shakespear: ", message)
                    self.app.channel_list[username].append(("Shakespear: ", message))
                    
                    
                else:
                
                    if  self.active_chat == username:
                        #chat_screen.add_message(username, message)
                        self.app.channel_list[username].append((username, message))
                        
                
                
        except Exception as e:
            logging.debug(f"UI update error: {e}")

if __name__ == "__main__":
    app = LayoutApp()
    app.run()