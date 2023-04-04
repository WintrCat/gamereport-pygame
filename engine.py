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
    moves: list[str] = []
    evals: list[dict] = []
    classifications: list[str] = []

def startAnalysisThread():
    t = threading.Thread(target=analyse)
    t.start()

def analyse():
    global fenCache
    
    # initialise conversion board
    board = chess.Board()

    # list of moves from pgn and empty list of evaluations
    moves: list[str] = extract_moves()
    evals: list[dict] = [engine.get_evaluation()]

    print("bruh")
    for move in moves:
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