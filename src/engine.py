import sys
import threading
import chess
import stockfish
import pgn

engine = stockfish.Stockfish("stockfish/stockfish-windows-2022-x86-64-avx2.exe")

if len(sys.argv) > 1 and sys.argv[1].isdigit():
    engine.set_depth(int(sys.argv[1]))
else:
    engine.set_depth(18)

def get(): 
    return engine

def extract_moves():
    moves = []

    game: pgn.PGNGame = pgn.loads(open("game.pgn", "r").read())[0]
    for token in game.moves:
        if not token.startswith("{"):
            moves.append(token)

    return moves[:-1]

#
# ANALYSIS ALGORITHM
#
class AnalysisResults:
    complete: bool = False
    sanMoves: list[str] = []
    board: chess.Board = None
    evals: list[dict] = []
    topMoves: list[list[dict]] = []
    classifications: list[str] = []

def startAnalysisThread():
    t = threading.Thread(target=analyse)
    t.start()

progress = [0, 1, False]
def get_analysis_progress():
    return progress

results = AnalysisResults()
def get_analysis_results():
    return results

def analyse():
    global progress, results
    
    # initialise conversion board
    board = chess.Board()

    # list of moves from pgn and empty list of evaluations
    moves: list[str] = extract_moves()
    evals: list[dict] = [engine.get_evaluation()]
    topMoves: list[list[dict]] = [engine.get_top_moves(2)]

    # collect evaluations and top moves from each move in the game
    for moveCount, move in enumerate(moves):
        # push move to conversion board
        board.push_san(move)

        # get uci from conversion board and transfer to internal engine board
        engine.make_moves_from_current_position([
            board.move_stack[-1].uci()
        ])

        # evaluate position after this move and add eval and top moves to list
        topMoves.append(engine.get_top_moves(2))
        evals.append(engine.get_evaluation())

        # update progress
        progress = [moveCount + 1, len(moves), True]

    # generate classifications from evaluation differences
    classifications: list[str] = []
    moveIndex = 0
    for prevEval, currEval in zip(evals, evals[1:]):
        # calculate evaluation difference
        diff = abs(currEval["value"] - prevEval["value"])

        # if there is only one legal move here apply forced
        if len(topMoves[moveIndex]) == 1:
            classifications.append("forced")
            moveIndex += 1
            continue

        # if no mate is involved in this move
        if prevEval["type"] == "cp" and currEval["type"] == "cp":
            # if difference is illegal (higher than 0 in better direction) reset diff
            if moveIndex % 2 == 0 and currEval["value"] > prevEval["value"]:
                diff = 0
            elif moveIndex % 2 == 1 and currEval["value"] < prevEval["value"]:
                diff = 0

            # apply classification based on eval difference
            if diff < 10:
                classifications.append("best")
            elif diff < 50:
                classifications.append("excellent")
            elif diff < 120:
                classifications.append("good")
            elif diff < 180:
                classifications.append("inaccuracy")
            elif diff < 270:
                classifications.append("mistake")
            else:
                classifications.append("blunder")

        # if it was mate and its still mate
        # if mate is closer, apply best
        # if mate is still the same distance away, apply excellent
        # if mate is made further by 3 or less moves, apply good
        # if mate is made further by more than 3 moves, apply inaccuracy
        elif prevEval["type"] == "mate" and currEval["type"] == "mate":
            if currEval["value"] == prevEval["value"]:
                classifications.append("excellent")
                moveIndex += 1
                continue

            # if mate in favour of white
            if prevEval["value"] > 0:
                print(prevEval)
                print(currEval)   
                if currEval["value"] < prevEval["value"]:
                    classifications.append("best")
                elif currEval["value"] <= prevEval["value"] + 3:
                    classifications.append("good")
                else:
                    classifications.append("inaccuracy")
            # if mate in favour of black (mate is negative)
            else:
                if currEval["value"] > prevEval["value"]:
                    classifications.append("best")
                elif currEval["value"] >= prevEval["value"] - 3:
                    classifications.append("good")
                else:
                    classifications.append("inaccuracy")

        # if it was mate and its no longer mate
        # if it was originally mate in 1 - 2, apply blunder
        # if it was originally mate in 3 - 5, apply mistake
        # if it was originally mate in 6 - 8, apply inaccuracy
        # if it was originally mate in 9+, apply good
        elif prevEval["type"] == "mate" and currEval["type"] == "cp":
            prevValue = abs(prevEval["value"])
            if prevValue <= 2:
                classifications.append("blunder")
            elif prevValue <= 5:
                classifications.append("mistake")
            elif prevValue <= 8:
                classifications.append("inaccuracy")
            else:
                classifications.append("good")

        # if it was not mate but the move allowed forced mate
        # if the allowed mate is mate in 1 - 2, apply blunder etc.
        # follow same rules as above
        elif prevEval["type"] == "cp" and currEval["type"] == "mate":
            currValue = abs(currEval["value"])
            if currValue <= 2:
                classifications.append("blunder")
            elif currValue <= 5:
                classifications.append("mistake")
            elif currValue <= 8:
                classifications.append("inaccuracy")
            else:
                classifications.append("good")

        moveIndex += 1
    
    results.complete = True
    results.sanMoves = moves
    results.board = board
    results.evals = evals
    results.topMoves = topMoves
    results.classifications = classifications