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
def is_piece_safe(board: chess.Board, square: chess.Square) -> bool:
    piece = board.piece_at(square)
    if piece.piece_type == chess.PAWN: return True

    attackers = board.attackers(not piece.color, square)
    defenders = board.attackers(piece.color, square)

    # remove king as an attacker if there are any defenders
    if len(defenders) > 0:
        for attackerSquare in attackers:
            if board.piece_at(attackerSquare).piece_type == chess.KING:
                attackers.remove(attackerSquare)
                break

    # if there are no attackers on the piece, it is defended
    if len(attackers) == 0: return True

    # if there are no legal captures of this piece, it is defended
    legallyCapturable = False
    for move in board.generate_legal_captures():
        if move.to_square == square:
            legallyCapturable = True
            break
    if not legallyCapturable: return True

    # even with more defense than attack, if piece is being attacked by piece of lower value, it is undefended
    # if it's being attacked by a king, only give undefended if there are no defenders
    for attackerSquare in attackers:
        if board.piece_at(attackerSquare).piece_type == chess.KING:
            return False
        elif pieceValues[board.piece_at(attackerSquare).piece_type] < pieceValues[piece.piece_type]:
            return False

    # calculate if piece was just equally or favourably traded
    move = board.pop()
    previousPiece = board.piece_at(square)
    wasExchanged = previousPiece != None and pieceValues[previousPiece.piece_type] >= pieceValues[piece.piece_type]
    board.push(move)

    # if there are more attackers than defenders and it was not just traded, it is undefended
    if len(attackers) > len(defenders) and not wasExchanged:
        return False
    else:
        return True