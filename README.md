# CS457 Quiz Game

This is a quiz game to allow students to brush up on CS457 material before exams

**Instructions:**
1. **Install dependencies:** <br/>
Make sure you're at the top folder and run `pip3 install -r requirements.txt`
2. **Source the environment:** <br/>
Run `set -a && source .env`
3. **Start the server:** <br/>
Run `python3 src/server/server.py` and specify a port to listen on
4. **Connect client to the server:** <br/>
Run `python3 src/client/client.py` and specify the server's IP address and port number
5. **Test the client UI:** <br/>
Run `python3 src/client/display/initialize.py` script to test the client UI

**Technologies used:**
* Python
* Sockets
* JSON
* curses

**Additional resources:**
* [Link to Game Tutorial](docs/game-tutorial.md)
* [Link to Team 5 SOW](docs/SOW.md)
* [Link to Python Documentation](docs/python-docs.md)
