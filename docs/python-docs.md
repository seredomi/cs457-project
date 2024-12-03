# Python Docs
This will serve as a brief description of the project structure.

## General Architecture
<img width="1968" alt="image" src="https://github.com/user-attachments/assets/0d2a5466-9991-4f51-8bba-0699affbcd2b">


## File Descriptions
### Utils
- `logger.py`
  - defines loggers that write all logs DEBUG and up to log files (separately specified by client/server) and all logs ERROR and up to stdout
- `messages.py`
  - contains generic methods for sending and receiving messages, including JSON schema validation
  - also contains mocks for each message type to enable testing
- `message_schemas`
  - contains JSON schemas for each message type
### Server
- `server.py`
  - contains all logic to handle multiple players and run multiple game sessions, as well as print current info tables to stdout
- `game_class.py`
  - class for a Game. includes logic for storing, updating, and retreiving info about a Game
- `player_class.py`
  - class for representing players. assignes unique IDs to them in addition to usernames, provides logic for storing, updating, and retreiving info about a Player
- `data`
  - contains all chapter quiz data in json format as well as the general chapter schema
  - contains `loader.py`, which transforms all the quiz data into python data structures
### Client
- `client.py`
  - holds all logic for communicating with server
  - tracks current users, active games, and current quiz info
- `ui.py`
  - contains all of the urwid logic for displaying menus, handling keystrokes and input submissions, displaying questions, and displaying quiz results
