# Python Docs
This will serve as a brief description of the project structure.

## General Architecture
![image](https://github.com/user-attachments/assets/b10c872e-c251-4aff-8feb-371bc4054fe8)

## File Descriptions
### Shared
- `messages.py`
  - contains generic methods for sending and receiving messages, including JSON schema validation
  - also contains mocks for each message type to enable testing
- `message_schemas`
  - contains JSON schemas for each message type
### Server
- `server.py`
  - contains all logic to handle multiple players and run multiple game sessions
- `game_class.py`
  - class for a Game. includes logic for allowing users to create, own, join, and delete games, as well as advance through questions, though we haven't implemented those message protocols yet
- `player_class.py`
  - class for representing players. assignes unique IDs to them in addition to usernames, and allows users to 
- `quiz_data`
  - contains all quiz data in json format as well as their schema
  - contains `data_loader.py`, which transforms all the quiz data into python data structures 
### Client
- `client.py`
  - holds all logic for communicating with server
  - tracks current users, active games, and current quiz info
- `dialogs.py`
  - contains all of the cli call and response dialogs needed to gather game config from the user. also houses the quiz question dialog, though that isn't implemented yet
- `display`
  - experimental UI stuff. not currently in use
