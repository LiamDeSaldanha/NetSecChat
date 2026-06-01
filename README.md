# Secure Asynchronous Cryptography Chat

This project implements a simplified version of the WireGuard protocol (https://www.wireguard.com/protocol/). As a user, there are different options for connecting to a central server—cleartext, encryption, and an extended encryption using cookies and a mac2 calculation. The messages and application allow users to send messages to other users, to create, join and leave channels, and send messages on channels. It also allows for features such as changing your username and retrieving information about channels and other users.

# Getting Started
## 1. Setup

**1.1 Create a virtual environment**
```bash
python -m venv .venv
```

**1.2 Activate the virtual environment**

| Platform | Shell | Command |
|---|---|---|
| Windows | PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows | Command Prompt | `.\.venv\Scripts\activate.bat` |
| Windows | Git Bash / WSL | `source .venv/Scripts/activate` |
| macOS / Linux | bash / zsh | `source .venv/bin/activate` |

**1.3 Install dependencies**
```bash
pip install -r requirements.txt
```

## 2. Store your static private key
Create a .env file in the same directory as the other files and add your static private key.
It needs to be in the following format:
```
my_static_private = YOUR_KEY_HERE
``` 
*Note the lack of quotation marks. Simply add the private key as is*

## 3. Run the client side code
To run the code, open a terminal and type 
```
python tui.py
```
This runs the terminal user interface (TUI), which is the point of interaction between the user and the server.
In the TUI, use the /help command for a list of commands. Clicking on a user or channel on the sidebar will open that specific chat, and the sidebar refreshes automatically to show which users and channels are active.