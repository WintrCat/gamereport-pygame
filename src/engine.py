import threading
import csv
import chess
import stockfish
import pgn
import accuracy

openingBook = csv.reader(open("openings.csv", "r"))

engine = stockfish.Stockfish("stockfish/stockfish-windows-2022-x86-64-avx2.exe")

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
    openings: list[str] = []
    sanMoves: list[str] = []
    board: chess.Board = None
    evals: list[dict] = []
    topMoves: list[list[dict]] = []
    classifications: list[str] = []
    accuracies: list[float] = []

def startAnalysisThread():
    t = threading.Thread(target=analyse)
    t.start()

progress = [0, 1, False]
def get_analysis_progress():
    return progress

results = AnalysisResults()
def get_analysis_results():
    return results

def set_analysis_results(loadedResults: AnalysisResults):
    global results
    results = loadedResults

def analyse():
    global progress, results
    
    # initialise conversion board
    board = chess.Board()

    # list of moves from pgn and empty list of evaluations
    # collects fen positions during game and used to find opening name
    fens: list[str] = []
    # list of opening names used to show opening name at different stages of game
    openings: list[str] = []
    # list of SAN moves
    moves: list[str] = extract_moves()
    # list of engine evaluations
    evals: list[dict] = [engine.get_evaluation()]
    # list of top move lists for each stage in the game (uci format)
    topMoves: list[list[dict]] = [engine.get_top_moves(2)]

    # list of attacker count on each move (used to identify free pieces for great/best detection)
    attackerCounts: list[list[int]] = []
    # if each move was a check
    checks: list[bool] = []

    #
    # COLLECT EVALUATIONS AND TOP ENGINE LINES
    #
    for moveCount, move in enumerate(moves):
        # push move to conversion board and store fen
        board.push_san(move)
        fens.append(board.fen().split(" ")[0])

        # get uci from conversion board and transfer to internal engine board
        engine.make_moves_from_current_position([
            board.move_stack[-1].uci()
        ])

        # evaluate position after this move and add eval and top moves to list
        topMoves.append(engine.get_top_moves(2))
        evals.append(engine.get_evaluation())

        # store count of attackers on piece that just moved (white and black attackers stored seperately)
        attackerCounts.append([
            len(board.attackers(chess.WHITE, board.move_stack[-1].to_square)),
            len(board.attackers(chess.BLACK, board.move_stack[-1].to_square))
        ])
        # store if move was a check
        checks.append(board.is_check())

        # update progress
        progress = [moveCount + 1, len(moves), True]

    #
    # GENERATE CLASSIFICATIONS
    #
    classifications: list[str] = []
    moveIndex = 0
    for prevEval, currEval in zip(evals, evals[1:]):
        # if board fen is in the opening book, apply book and skip to next eval
        isBook = False
        for opening in openingBook:
            if fens[moveIndex] == opening[1]:
                classifications.append("book")
                openings.append(opening[0])
                moveIndex += 1
                isBook = True
                break
        if isBook: continue

        # if there is only one legal move here apply forced and skip to next eval
        if len(topMoves[moveIndex]) == 1:
            classifications.append("forced")
            moveIndex += 1
            continue

        # if it is top engine move give best even if there is residue difference and skip to next eval
        if topMoves[moveIndex][0]["Move"] == board.move_stack[moveIndex].uci():
            endClassification = "best"

            # if both top moves are not mate (no mate line is currently on the board)
            if topMoves[moveIndex][0]["Centipawn"] != None and topMoves[moveIndex][1]["Centipawn"] != None:
                # if second best move is significantly worse than first best move, consider great
                moveColour = moveIndex % 2

                if ((moveColour == 0 and topMoves[moveIndex][0]["Centipawn"] >= topMoves[moveIndex][1]["Centipawn"] + 210)
                or
                (moveColour == 1 and topMoves[moveIndex][0]["Centipawn"] <= topMoves[moveIndex][1]["Centipawn"] - 210)
                or 
                (moveColour == 0 and topMoves[moveIndex][0]["Centipawn"] >= topMoves[moveIndex][1]["Centipawn"] + 110 and topMoves[moveIndex][1]["Centipawn"] < 0)
                or 
                (moveColour == 1 and topMoves[moveIndex][0]["Centipawn"] <= topMoves[moveIndex][1]["Centipawn"] - 110) and topMoves[moveIndex][1]["Centipawn"] > 0):
                    
                    # pre-emptively give great, and then demote after checks
                    endClassification = "great"

                    # if this move was a capture and the piece was less or undefended, do not give great
                    if "x" in moves[moveIndex] and attackerCounts[moveIndex][moveColour] >= attackerCounts[moveIndex][(moveColour + 1) % 2]:
                        endClassification = "best"
                    
                    # if the move before this was a check, do not give great
                    if moveIndex > 0 and checks[moveIndex - 1]:
                        endClassification = "best"

            classifications.append(endClassification)
            moveIndex += 1
            continue

        # calculate evaluation difference
        diff = abs(currEval["value"] - prevEval["value"])

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
        # if mate is getting closer apply best
        # if mate is still same distance apply excellent
        # if mate is 9 or less moves further away apply good
        # otherwise apply inaccuracy, mate is there but is too far for average player
        elif prevEval["type"] == "mate" and currEval["type"] == "mate":
            if currEval["value"] == prevEval["value"]:
                classifications.append("excellent")
                moveIndex += 1
                continue

            # if mate in favour of white
            if prevEval["value"] > 0:
                if currEval["value"] < prevEval["value"]:
                    classifications.append("best")
                elif currEval["value"] <= prevEval["value"] + 9:
                    classifications.append("good")
                else:
                    classifications.append("inaccuracy")
            # if mate in favour of black (mate is negative)
            else:
                if currEval["value"] > prevEval["value"]:
                    classifications.append("best")
                elif currEval["value"] >= prevEval["value"] - 9:
                    classifications.append("good")
                else:
                    classifications.append("inaccuracy")

        # if it was mate and its no longer mate
        # if it was originally mate in 1 - 2, apply mistake
        # if it was originally mate in 3 - 5, apply inaccuracy
        # if it was originally mate in 6 - 8, apply good
        # if it was originally mate in 9+, apply excellent
        elif prevEval["type"] == "mate" and currEval["type"] == "cp":
            prevValue = abs(prevEval["value"])
            if prevValue <= 2:
                classifications.append("mistake")
            elif prevValue <= 5:
                classifications.append("inaccuracy")
            elif prevValue <= 8:
                classifications.append("good")
            else:
                classifications.append("excellent")

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
            elif currValue <= 14:
                classifications.append("good")
            else:
                classifications.append("excellent")

        moveIndex += 1
    
    # dump analysis results into AnalysisResults object
    results.complete = True
    results.openings = openings
    results.sanMoves = moves
    results.board = board
    results.evals = evals
    results.topMoves = topMoves
    results.classifications = classifications

    # save accuracy percentages based on dumped classifications
    accuracy.set_white_accuracy(accuracy.calculate_accuracy(chess.WHITE))
    accuracy.set_black_accuracy(accuracy.calculate_accuracy(chess.BLACK))
    results.accuracies = [accuracy.get_white_accuracy(), accuracy.get_black_accuracy()]