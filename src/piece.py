import chess

pieceValues = {
    chess.PAWN: 1,
    chess.KING: 2,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9
}

# determines and returns whether a piece on a board is safe (defended / traded) or unsafe (hanging)
def is_piece_safe(board: chess.Board, square: chess.Square, debug = False) -> bool:
    piece = board.piece_at(square)
    if piece.piece_type == chess.PAWN: return True

    attackers = board.attackers(not piece.color, square)
    defenders = board.attackers(piece.color, square)
    if debug:
        print("Attackers: " + str(len(attackers)))
        print("Defenders: " + str(len(defenders)))

    # remove king as an attacker if there are any defenders
    if len(defenders) > 0:
        for attackerSquare in attackers:
            if board.piece_at(attackerSquare).piece_type == chess.KING:
                attackers.remove(attackerSquare)
                break

    # if there are no attackers on the piece, it is defended
    if len(attackers) == 0:
        if debug: print("No attackers, so is defended")
        return True

    # if there are no legal captures of this piece, it is defended
    legallyCapturable = False
    for move in board.generate_legal_captures():
        if move.to_square == square:
            legallyCapturable = True
            break
    if not legallyCapturable: 
        if debug: print("No legal captures of it so it's defended")
        return True
    
    # calculate if piece was just equally or favourably traded
    move = board.pop()
    previousPiece = board.piece_at(square)
    wasExchanged = (
        previousPiece != None 
        and pieceValues[previousPiece.piece_type] >= pieceValues[piece.piece_type] 
        and previousPiece.color != piece.color
    )
    board.push(move)
    if debug: print("Was the piece just exchanged equally or favourably: " + str(wasExchanged))

    # even with more defense than attack, if piece is being attacked by piece of lower value, it is undefended
    # if it's being attacked by a king, only give undefended if there are no defenders
    if not wasExchanged:
        for attackerSquare in attackers:
            if board.piece_at(attackerSquare).piece_type == chess.KING:
                return False
            elif pieceValues[board.piece_at(attackerSquare).piece_type] < pieceValues[piece.piece_type]:
                return False

    # if there are more attackers than defenders and it was not just traded, it is undefended
    if len(attackers) > len(defenders) and not wasExchanged:
        return False
    else:
        if debug: print("There are either less attackers than defenders or it was just traded off")
        return True