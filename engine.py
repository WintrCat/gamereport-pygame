import threading
import chess
import stockfish
import pgn
import pygame

engine = stockfish.Stockfish("stockfish/stockfish-windows-2022-x86-64-avx2.exe")
engine.set_depth(18)

fenCache = engine.get_fen_position()

def get(): 
    return engine

def get_fen():
    return fenCache

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
    board: chess.Board = None
    evals: list[dict] = []
    classifications: list[str] = []

def startAnalysisThread():
    t = threading.Thread(target=analyse)
    t.start()

progress = [0, 1]
def get_analysis_progress():
    return progress

results = AnalysisResults()
def get_analysis_results():
    return results

def analyse():
    global fenCache, progress, results
    
    # initialise conversion board
    board = chess.Board()

    # list of moves from pgn and empty list of evaluations
    moves: list[str] = extract_moves()
    evals: list[dict] = [engine.get_evaluation()]

    # collect evaluations from each move in the game
    for moveCount, move in enumerate(moves):
        # push move to conversion board
        board.push_san(move)

        # get uci from conversion board and transfer to internal engine board
        engine.make_moves_from_current_position([
            board.move_stack[-1].uci()
        ])

        # update fen cache with new fen position
        fenCache = board.fen()

        # evaluate position after this move and add to list
        evals.append(engine.get_evaluation())
        print(evals[-1])

        # update progress
        progress = [moveCount + 1, len(moves)]

    # generate classifications from evaluation differences
    classifications: list[str] = []
    for prev_eval, curr_eval in zip(evals, evals[1:]):
        # calculate evaluation difference
        diff = abs(curr_eval["value"] - prev_eval["value"])

        # if no mate is involved in this move
        if prev_eval["type"] == "cp" and curr_eval["type"] == "cp":
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
    
    results.complete = True
    results.board = board
    results.evals = evals
    results.classifications = classifications