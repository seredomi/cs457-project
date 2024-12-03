# CS457 Quiz Game

**Description:**

In this game, you can choose different CS 457 chapters to quiz yourself on. \
After starting a new game, you'll receive questions from the chosen chapters in random order. You can answer all the questions you selected, or quit whenever you want. \
If you'd like to compete with friends, they can join the same server as you and answer each question at the same time! \
To get started, see the instructions below.

**Instructions:**
1. **Install dependencies:** <br/>
Make sure you're at the top folder and run `python3 -m pip3 install -r requirements.txt`
2. **Start the server:** <br/>
Run `./run-server.sh [IP] [port]`
3. **Connect client to the server:** <br/>
Run `./run-client.sh [IP] [port]`
4. You're all set to start playing. For detailed instructions on gameplay, see the [Game Tutorial](docs/game-tutorial.md)

**Technologies used:**
* Python
* Sockets
* JSON
* Urwid

**Additional resources:**
* [Link to Game Tutorial](docs/game-tutorial.md)
* [Link to Team 5 SOW](docs/SOW.md)
* [Link to Python Documentation](docs/python-docs.md)
