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

def extractMoves():
    moves = []

    game: pgn.PGNGame = pgn.loads(open("game.pgn", "r").read())[0]
    for token in game.moves:
        if not token.startswith("{"):
            moves.append(token)

    return moves[:-1]

#
# ANALYSIS ALGORITHM
#
pieceValues = {
    chess.PAWN: 1,
    chess.KING: 2,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9
}

class AnalysisResults:
    complete: bool = False

    boardStates: list[chess.Board] = []

    # sans for convenience (board only has uci by default)
    sans: list[str] = []

    # opening book
    openings: list[str] = []

    # analysis
    evals: list[dict] = [engine.get_evaluation()]
    topMoves: list[list[dict]] = [engine.get_top_moves(2)]
    classifications: list[str] = []
    accuracies: list[float] = []

    def __getstate__(self) -> dict:
        return {
            "complete": self.complete,
            "boardStates": self.boardStates[-1].move_stack,
            "sans": self.sans,
            "openings": self.openings,
            "evals": self.evals,
            "topMoves": self.topMoves,
            "classifications": self.classifications,
            "accuracies": self.accuracies
        }
    
    def __setstate__(self, cucumber: dict):
        self.complete = cucumber.get("complete", True)

        moves = cucumber.get("boardStates", [])
        for moveIndex in range(len(moves)):
            board = chess.Board()
            for i in range(moveIndex + 1):
                board.push(moves[i])
            self.boardStates.append(board)

        self.sans = cucumber.get("sans", [])

        self.openings = cucumber.get("openings", [])

        self.evals = cucumber.get("evals", [])
        self.topMoves = cucumber.get("topMoves", [])
        self.classifications = cucumber.get("classifications", [])
        self.accuracies = cucumber.get("accuracies", [])


def startAnalysisThread():
    t = threading.Thread(target=analyse)
    t.start()

# how many moves have been analysed, has analysis started
progress = [0, False]
def get_analysis_progress():
    return progress

results = AnalysisResults()
def get_results():
    return results
def set_results(loadedResults: AnalysisResults):
    global results
    results = loadedResults

def analyse():
    global progress, results

    #
    # COLLECT EVALUATIONS AND TOP ENGINE LINES
    #

    # add starting position board state to make copies of
    results.boardStates = [chess.Board()]

    results.sans = extractMoves()
    for moveCount, move in enumerate(results.sans):
        # push new board state
        currentBoard = results.boardStates[-1].copy()
        currentBoard.push_san(move)
        results.boardStates.append(currentBoard)

        # get uci from conversion board and transfer to internal engine board
        engine.make_moves_from_current_position([currentBoard.peek().uci()])

        # evaluate position after this move and add eval and top moves to list
        results.evals.append(engine.get_evaluation())
        results.topMoves.append(engine.get_top_moves(2))

        # update progress
        progress = [moveCount + 1, True]

    # remove first board state (it was the starting pos and was only used to make copies of)
    results.boardStates.pop(0)

    #
    # GENERATE CLASSIFICATIONS
    #
    moveIndex = 0
    for prevEval, currEval in zip(results.evals, results.evals[1:]):
        # current and previous board state
        currentState = results.boardStates[moveIndex]
        previousState = results.boardStates[moveIndex - 1]

        # if board fen is in the opening book, apply book and skip to next eval
        isBook = False
        for opening in openingBook:
            if currentState.fen().split(" ")[0] == opening[1]:
                results.classifications.append("book")
                results.openings.append(opening[0])
                isBook = True
                break
        if isBook:
            moveIndex += 1
            continue

        # if there is only one legal move here apply forced and skip to next eval
        if len(results.topMoves[moveIndex]) == 1:
            results.classifications.append("forced")
            moveIndex += 1
            continue

        # if it is top engine move give best even if there is residue difference and skip to next eval
        if results.topMoves[moveIndex][0]["Move"] == currentState.peek().uci():
            endClassification = "best"

            # if both top moves are not mate (no mate line is currently on the board)
            if results.topMoves[moveIndex][0]["Centipawn"] != None and results.topMoves[moveIndex][1]["Centipawn"] != None:
                # if second best move is significantly worse than first best move, consider great
                moveColour = moveIndex % 2
                if ((moveColour == 0 and results.topMoves[moveIndex][0]["Centipawn"] >= results.topMoves[moveIndex][1]["Centipawn"] + 180)
                or
                (moveColour == 1 and results.topMoves[moveIndex][0]["Centipawn"] <= results.topMoves[moveIndex][1]["Centipawn"] - 180)
                or 
                (moveColour == 0 and results.topMoves[moveIndex][0]["Centipawn"] >= results.topMoves[moveIndex][1]["Centipawn"] + 110 and results.topMoves[moveIndex][1]["Centipawn"] < 0)
                or 
                (moveColour == 1 and results.topMoves[moveIndex][0]["Centipawn"] <= results.topMoves[moveIndex][1]["Centipawn"] - 110) and results.topMoves[moveIndex][1]["Centipawn"] > 0):
                    
                    # pre-emptively give great, and then edit after checks
                    endClassification = "great"

                    # if this move was a capture and the piece was less or undefended, do not give great
                    attackerCount = len(currentState.attackers(moveColour == 0, currentState.peek().to_square))
                    defenderCount = len(currentState.attackers(moveColour != 0, currentState.peek().to_square))
                    if "x" in results.sans[moveIndex] and attackerCount >= defenderCount:
                        endClassification = "best"
                    
                    # if the move before this was a check, do not give great
                    if moveIndex > 0 and results.boardStates[moveIndex - 1].is_check():
                        endClassification = "best"

                    # if the move was a sacrifice, give brilliant
                    for square in chess.SQUARES:
                        # get piece at this square
                        piece = currentState.piece_at(square)
                        # if this piece is owned by player who made this move
                        if piece != None and piece.color == (moveColour == 0):
                            # get enemy attackers and ally defenders on that piece
                            attackers = currentState.attackers(moveColour != 0, square)
                            defenders = currentState.attackers(moveColour == 0, square)

                            # check if move was equal or favourable exchange
                            wasMoveExchange = False
                            previousPiece = previousState.piece_at(square)
                            if (
                                previousPiece != None
                                and previousPiece.color == (moveColour != 0) 
                                and pieceValues[previousPiece.piece_type] >= pieceValues[piece.piece_type]
                            ):
                                wasMoveExchange = True

                            if (
                                len(attackers) > len(defenders) 
                                and pieceValues[currentState.piece_at(square).piece_type] > 1
                                and not wasMoveExchange
                            ):
                                endClassification = "brilliant"
                                break

                            for attackerSquare in attackers:
                                # if attacker is a king only give brilliant if piece is undefended
                                if currentState.piece_at(attackerSquare).piece_type == chess.KING:
                                    if len(defenders) == 0:
                                        endClassification = "brilliant"
                                        break

                                # if value of attacking piece is lower than your piece
                                elif pieceValues[currentState.piece_at(attackerSquare).piece_type] < pieceValues[piece.piece_type]:
                                    endClassification = "brilliant"
                                    break

            results.classifications.append(endClassification)
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
                results.classifications.append("best")
            elif diff < 50:
                results.classifications.append("excellent")
            elif diff < 120:
                results.classifications.append("good")
            elif diff < 180:
                results.classifications.append("inaccuracy")
            elif diff < 270:
                results.classifications.append("mistake")
            else:
                results.classifications.append("blunder")

        # if it was mate and its still mate
        # if mate is getting closer apply best
        # if mate is still same distance apply excellent
        # if mate is 9 or less moves further away apply good
        # otherwise apply inaccuracy, mate is there but is too far for average player
        elif prevEval["type"] == "mate" and currEval["type"] == "mate":
            if currEval["value"] == prevEval["value"]:
                results.classifications.append("excellent")
                moveIndex += 1
                continue

            # if mate in favour of white
            if prevEval["value"] > 0:
                if currEval["value"] < prevEval["value"]:
                    results.classifications.append("best")
                elif currEval["value"] <= prevEval["value"] + 9:
                    results.classifications.append("good")
                else:
                    results.classifications.append("inaccuracy")
            # if mate in favour of black (mate is negative)
            else:
                if currEval["value"] > prevEval["value"]:
                    results.classifications.append("best")
                elif currEval["value"] >= prevEval["value"] - 9:
                    results.classifications.append("good")
                else:
                    results.classifications.append("inaccuracy")

        # if it was mate and its no longer mate
        # if it was originally mate in 1 - 2, apply mistake
        # if it was originally mate in 3 - 5, apply inaccuracy
        # if it was originally mate in 6 - 8, apply good
        # if it was originally mate in 9+, apply excellent
        elif prevEval["type"] == "mate" and currEval["type"] == "cp":
            prevValue = abs(prevEval["value"])
            if prevValue <= 2:
                results.classifications.append("mistake")
            elif prevValue <= 5:
                results.classifications.append("inaccuracy")
            elif prevValue <= 8:
                results.classifications.append("good")
            else:
                results.classifications.append("excellent")

        # if it was not mate but the move allowed forced mate
        # if the allowed mate is mate in 1 - 2, apply blunder etc.
        # follow same rules as above
        elif prevEval["type"] == "cp" and currEval["type"] == "mate":
            currValue = abs(currEval["value"])
            if currValue <= 2:
                results.classifications.append("blunder")
            elif currValue <= 5:
                results.classifications.append("mistake")
            elif currValue <= 8:
                results.classifications.append("inaccuracy")
            elif currValue <= 14:
                results.classifications.append("good")
            else:
                results.classifications.append("excellent")

        moveIndex += 1
    
    # set results completion to true
    results.complete = True

    # save accuracy percentages based on dumped classifications
    accuracy.set_white_accuracy(accuracy.calculate_accuracy(chess.WHITE))
    accuracy.set_black_accuracy(accuracy.calculate_accuracy(chess.BLACK))
    results.accuracies = [accuracy.get_white_accuracy(), accuracy.get_black_accuracy()]