# **WintrCat's Game Report**

### **About**:
A Python program by wintrcat that provides game reports for your chess games, without the need to pay for the Diamond premium on Chess.com. A locally installed instance of Stockfish 15.1 is used (Chess.com only uses 11!) to evaluate your moves, which the program then classifies and gives insights into. 

### **Usage**:
- Download the PGN file of the game you want to analyse; you can select and download Chess.com games from your game archive.
- Replace the game.pgn file in this directory with the one you downloaded; make sure to rename yours to game.pgn as well.
- Run `pip install -r requirements.txt` in a terminal to install all of the necessary libraries.
- Use the `cd` terminal command to enter the directory where this `README.md` file is.
- Run `python src/main.py` in a terminal to run the program.

#### **Command-Line Arguments:**
- `-d` / `--depth` Set the depth of the chess engine
- `-f` / `--file` Set the analysis savefile to load

Example command: `python src/main.py --depth 22 --file save.asys`

### **Engine Depth:**
The engine used for this program is Stockfish 15.1, although other versions installed locally can be used for this program and for the most part will be fine unless a very old version is used. The depth of the engine refers to how many moves ahead of time that the engine accounts for when evaluating moves in the game. A higher depth means a more accurate game report, but also one that takes longer to produce. The default depth is 18 (Chess.com's default depth) which produces reports for 50-move games in 20-30 seconds, although this can heavily depend on the power of your CPU. If you want a more in-depth report, you can use a depth of 22+ but this will become exponentially slower. Games on Chess.com are analysed on their servers which are generally faster than a desktop computer, which is why it can sometimes take a minute or so for the program to analyse a game.

### **Disclaimers**:
- Stockfish source code is not included in this repository. The source code has not been modified and is available @ https://github.com/official-stockfish/Stockfish
- pgn.py is not by me; copyright license for the library is included within its script file, `src/pgn.py`.