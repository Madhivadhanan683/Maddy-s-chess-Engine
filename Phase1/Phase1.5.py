#!/usr/bin/env python3
"""
Phase 1.5 Chess Engine (alpha-beta pruning, algebraic input with case sensitivity)

Features:
- Algebraic input: e4, Nf3, exd5, nf6 (lowercase piece letter => black piece)
- Turn enforcement (white_to_move)
- Full pseudo-legal move generation for all pieces (no castling/en-passant/promotion)
- Filters moves that leave own king in check
- Alpha-beta search for `go depth N`
- Perft for correctness testing
- Simple material evaluation
"""

import copy
import time
import math

# -------------------------
# Constants / Helpers
# -------------------------
WHITE_PIECES = set("PRNBQK")
BLACK_PIECES = set("prnbqk")
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

# starting board
def starting_board():
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]

def show_board(board):
    print("\n   a b c d e f g h")
    for r in range(8):
        print(f"{8 - r}  {' '.join(board[r])}  {8 - r}")
    print("   a b c d e f g h\n")

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def square_to_index(sq):
    """sq like 'e4' -> (row, col)"""
    if len(sq) != 2: raise ValueError("Bad square")
    col = ord(sq[0]) - ord('a')
    row = 8 - int(sq[1])
    return row, col

def index_to_square(r, c):
    return chr(c + ord('a')) + str(8 - r)

# -------------------------
# Move generation & legality
# -------------------------
def clear_path(board, r1, c1, r2, c2):
    dr = 0 if r2 == r1 else (1 if r2 > r1 else -1)
    dc = 0 if c2 == c1 else (1 if c2 > c1 else -1)
    steps = max(abs(r2 - r1), abs(c2 - c1))
    for i in range(1, steps):
        if board[r1 + dr * i][c1 + dc * i] != '.':
            return False
    return True

def is_pseudo_legal(board, r1, c1, r2, c2):
    """Does not check king-safety. Only geometry and captures"""
    if not (in_bounds(r1, c1) and in_bounds(r2, c2)):
        return False
    piece = board[r1][c1]
    if piece == '.': return False
    target = board[r2][c2]
    # can't capture own piece
    if target != '.' and (target.isupper() == piece.isupper()):
        return False
    dr = r2 - r1
    dc = c2 - c1
    pu = piece.upper()

    if pu == 'P':
        color_white = piece.isupper()
        direction = -1 if color_white else 1
        start_row = 6 if color_white else 1
        # forward
        if dc == 0:
            if dr == direction and target == '.':
                return True
            if r1 == start_row and dr == 2*direction and board[r1+direction][c1] == '.' and target == '.':
                return True
            return False
        # capture
        if abs(dc) == 1 and dr == direction and target != '.':
            return True
        return False

    if pu == 'N':
        return (abs(dr), abs(dc)) in [(1,2),(2,1)]

    if pu == 'B':
        if abs(dr) != abs(dc): return False
        return clear_path(board, r1, c1, r2, c2)

    if pu == 'R':
        if dr != 0 and dc != 0: return False
        return clear_path(board, r1, c1, r2, c2)

    if pu == 'Q':
        if abs(dr)==abs(dc) or dr==0 or dc==0:
            return clear_path(board, r1, c1, r2, c2)
        return False

    if pu == 'K':
        return max(abs(dr), abs(dc)) == 1

    return False

def square_is_attacked(board, row, col, attacker_is_white):
    """
    Is square (row,col) attacked by side (attacker_is_white True => white)?
    We'll test pawn, knight, king, and sliding attackers.
    """
    # pawn attacks
    if attacker_is_white:
        # white pawns attack to north-west and north-east (i.e. row-1, col+-1)
        for dc in (-1, 1):
            r = row + 1  # since white pawns move up visually? Note: row 0 is rank8. For our coords white pawns move -1.
        # Correction: our indexing: row 0 is rank8. White pawns move from rank2 (row6) -> rank3 (row5) -> smaller row.
        # So white pawn attack squares are (row+1?) No — compute directly:
    # Simpler approach: check all attacker squares for knights/sliders/king/pawns by scanning offsets.

    # Knights
    knight_offsets = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
    for dr, dc in knight_offsets:
        r = row + dr
        c = col + dc
        if in_bounds(r,c):
            p = board[r][c]
            if p != '.':
                if attacker_is_white and p == 'N': return True
                if not attacker_is_white and p == 'n': return True

    # King (adjacent)
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr==0 and dc==0: continue
            r = row + dr; c = col + dc
            if in_bounds(r,c):
                p = board[r][c]
                if p != '.':
                    if attacker_is_white and p == 'K': return True
                    if not attacker_is_white and p == 'k': return True

    # Pawn attacks: if attacker is white, white pawns (P) attack to row-1 relative (since white moves 'up' decreasing row)
    if attacker_is_white:
        for dc in (-1, 1):
            r = row + 1  # incoming pawn would be below target (since pawn moves up => r_from = r+1)
            c = col + dc
            if in_bounds(r,c) and board[r][c] == 'P': return True
    else:
        for dc in (-1, 1):
            r = row - 1
            c = col + dc
            if in_bounds(r,c) and board[r][c] == 'p': return True

    # Sliding pieces: rook/queen on orthogonals
    directions = [(1,0),(-1,0),(0,1),(0,-1)]
    for dr, dc in directions:
        r, c = row+dr, col+dc
        while in_bounds(r,c):
            p = board[r][c]
            if p != '.':
                if attacker_is_white:
                    if p in ('R','Q'): return True
                else:
                    if p in ('r','q'): return True
                break
            r += dr; c += dc

    # Diagonals: bishop/queen
    directions = [(1,1),(1,-1),(-1,1),(-1,-1)]
    for dr, dc in directions:
        r, c = row+dr, col+dc
        while in_bounds(r,c):
            p = board[r][c]
            if p != '.':
                if attacker_is_white:
                    if p in ('B','Q'): return True
                else:
                    if p in ('b','q'): return True
                break
            r += dr; c += dc

    return False

def find_king(board, white_king=True):
    target = 'K' if white_king else 'k'
    for r in range(8):
        for c in range(8):
            if board[r][c] == target:
                return r, c
    return None

def is_in_check(board, white_king_side):
    king_pos = find_king(board, white_king_side)
    if not king_pos:
        return False
    kr, kc = king_pos
    # If white_king_side True, attackers are black
    return square_is_attacked(board, kr, kc, attacker_is_white=not white_king_side)

def generate_all_moves(board, white_to_move):
    """Generate pseudo-legal moves (tuples r1,c1,r2,c2) for side to move."""
    moves = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == '.': continue
            if white_to_move and not p.isupper(): continue
            if not white_to_move and not p.islower(): continue
            for r2 in range(8):
                for c2 in range(8):
                    if is_pseudo_legal(board, r, c, r2, c2):
                        moves.append((r,c,r2,c2))
    return moves

def generate_legal_moves(board, white_to_move):
    """Filter moves that leave own king not in check."""
    moves = []
    for m in generate_all_moves(board, white_to_move):
        r1,c1,r2,c2 = m
        captured = board[r2][c2]
        # make
        board[r2][c2] = board[r1][c1]
        board[r1][c1] = '.'
        incheck = is_in_check(board, white_to_move)
        # undo
        board[r1][c1] = board[r2][c2]
        board[r2][c2] = captured
        if not incheck:
            moves.append(m)
    return moves

# -------------------------
# Make / Unmake
# -------------------------
def make_move_on_board(board, move):
    r1,c1,r2,c2 = move
    captured = board[r2][c2]
    board[r2][c2] = board[r1][c1]
    board[r1][c1] = '.'
    return captured

def undo_move_on_board(board, move, captured):
    r1,c1,r2,c2 = move
    board[r1][c1] = board[r2][c2]
    board[r2][c2] = captured

# -------------------------
# Evaluation
# -------------------------
def evaluate(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == '.': continue
            v = PIECE_VALUES[p.upper()]
            score += v if p.isupper() else -v
    return score

# -------------------------
# Alpha-Beta Search
# -------------------------
nodes_searched = 0

def alphabeta(board, depth, alpha, beta, white_to_move):
    global nodes_searched
    nodes_searched += 1
    if depth == 0:
        return evaluate(board), None
    moves = generate_legal_moves(board, white_to_move)
    if not moves:
        # no legal moves: either checkmate or stalemate
        if is_in_check(board, white_to_move):
            # mate score: large negative for side to move
            return (-999999 if white_to_move else 999999), None
        else:
            return 0, None  # stalemate
    best_move = None
    # Simple move ordering: captures first
    moves.sort(key=lambda m: 0 if board[m[2]][m[3]] == '.' else 1, reverse=True)
    if white_to_move:
        value = -math.inf
        for m in moves:
            captured = make_move_on_board(board, m)
            val, _ = alphabeta(board, depth-1, alpha, beta, False)
            undo_move_on_board(board, m, captured)
            if val > value:
                value = val
                best_move = m
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = math.inf
        for m in moves:
            captured = make_move_on_board(board, m)
            val, _ = alphabeta(board, depth-1, alpha, beta, True)
            undo_move_on_board(board, m, captured)
            if val < value:
                value = val
                best_move = m
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move

# -------------------------
# Move parsing (algebraic + coords) with case-sensitivity rules
# -------------------------
def parse_user_move(board, move_str, white_to_move):
    """
    Accepts:
      - coordinate style: e2e4
      - algebraic: e4, exd5, Nf3, Bxd3, nf6 (lowercase piece letter -> black piece),
        'O-O', 'O-O-O' (not fully verified; basic).
    Returns a move tuple (r1,c1,r2,c2) or None if not found/illegal.
    """
    s = move_str.strip()
    # coordinates: e2e4
    if len(s) == 4 and s[0] in "abcdefgh" and s[2] in "abcdefgh":
        try:
            r1,c1 = square_to_index(s[:2])
            r2,c2 = square_to_index(s[2:])
            # quick validation of side-to-move ownership will be checked later
            if is_pseudo_legal(board, r1,c1,r2,c2):
                return (r1,c1,r2,c2)
            else:
                return None
        except:
            return None
    # castling (rudimentary)
    if s in ("O-O","o-o","0-0"):
        if white_to_move:
            # white kingside
            if board[7][4]=='K' and board[7][7]=='R' and board[7][5]=='.' and board[7][6]=='.':
                return (7,4,7,6)
        else:
            if board[0][4]=='k' and board[0][7]=='r' and board[0][5]=='.' and board[0][6]=='.':
                return (0,4,0,6)
        return None
    if s in ("O-O-O","o-o-o","0-0-0"):
        if white_to_move:
            if board[7][4]=='K' and board[7][0]=='R' and board[7][1]=='.' and board[7][2]=='.' and board[7][3]=='.':
                return (7,4,7,2)
        else:
            if board[0][4]=='k' and board[0][0]=='r' and board[0][1]=='.' and board[0][2]=='.' and board[0][3]=='.':
                return (0,4,0,2)
        return None

    # Algebraic: detect piece-letter (if present)
    # According to your rule: uppercase piece-letter => white piece; lowercase => black piece
    piece_letter = None
    desired_color_white = white_to_move
    # if first char is a letter in NBRQK or lowercase variants, that indicates piece and color
    if s and s[0] in "NBRQKnbrqk":
        piece_letter = s[0].upper()
        desired_color_white = s[0].isupper()
        s_body = s[1:]
    else:
        piece_letter = 'P'  # pawn
        desired_color_white = white_to_move
        s_body = s

    # strip capture marker and other markers like '+' or '#'
    s_body = s_body.replace('x','')
    s_body = s_body.replace('+','').replace('#','')

    # destination is last two chars
    if len(s_body) < 2:
        return None
    dest = s_body[-2:]
    try:
        r2,c2 = square_to_index(dest)
    except:
        return None

    # find candidate pieces of that type and color that can move to dest
    candidates = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == '.': continue
            if desired_color_white and not p.isupper(): continue
            if not desired_color_white and not p.islower(): continue
            if p.upper() != piece_letter: continue
            if is_pseudo_legal(board, r, c, r2, c2):
                # later we'll ensure king safety in generate_legal_moves; here we collect pseudo-legal
                candidates.append((r,c))

    if not candidates:
        return None

    # If there's disambiguation characters in s_body (like Nbd2 or R1e1), try to use them
    disamb = s_body[:-2]  # portion before destination (already had 'x' removed)
    if disamb:
        filtered = []
        for (r,c) in candidates:
            filec = chr(c + ord('a'))
            rankc = str(8 - r)
            if disamb in (filec, rankc, filec+rankc):
                filtered.append((r,c))
        if filtered:
            candidates = filtered

    # if multiple still, pick the first (phase 1.5 simplification)
    r1,c1 = candidates[0]
    # final check: side to move must match white_to_move
    if desired_color_white != white_to_move:
        # user explicitly asked upper/lower piece for opposite color — reject
        return None
    # return move tuple, but only if it's legal w.r.t king safety
    captured = board[r2][c2]
    board[r2][c2] = board[r1][c1]
    board[r1][c1] = '.'
    illegal = is_in_check(board, white_to_move)  # if our king is in check after move, illegal
    # undo
    board[r1][c1] = board[r2][c2]
    board[r2][c2] = captured
    if illegal:
        return None
    return (r1,c1,r2,c2)

# -------------------------
# SAN-ish formatting for display
# -------------------------
def move_to_san(board, move):
    r1,c1,r2,c2 = move
    piece = board[r1][c1]
    dest_piece = board[r2][c2]
    piece_letter = '' if piece.upper() == 'P' else piece.upper()
    capture = 'x' if dest_piece != '.' else ''
    if piece.upper() == 'P' and capture:
        return f"{chr(c1+ord('a'))}{capture}{index_to_square(r2,c2)}"
    else:
        return f"{piece_letter}{capture}{index_to_square(r2,c2)}"

# -------------------------
# Perft
# -------------------------
def perft(board, depth, white_to_move):
    if depth == 0:
        return 1
    nodes = 0
    moves = generate_legal_moves(board, white_to_move)
    for m in moves:
        captured = make_move_on_board(board, m)
        nodes += perft(board, depth-1, not white_to_move)
        undo_move_on_board(board, m, captured)
    return nodes

# -------------------------
# CLI / UCI-like loop
# -------------------------
def uci_loop():
    global nodes_searched
    board = starting_board()
    white_to_move = True
    print("Phase 1.5 Chess Engine — alpha-beta pruning")
    print("Commands: show | e4 | Nf3 | nf6 | go depth N | perft N | quit")
    show_board(board)

    while True:
        side = "White" if white_to_move else "Black"
        try:
            cmd = input(f"[{side}] > ").strip()
        except EOFError:
            break
        if not cmd:
            continue
        if cmd == "quit":
            break
        if cmd == "show":
            show_board(board)
            continue
        parts = cmd.split()
        if parts[0] == "perft" and len(parts) == 2:
            try:
                d = int(parts[1])
            except:
                print("bad depth")
                continue
            t0 = time.time()
            nodes = perft(board, d, white_to_move)
            t1 = time.time()
            print(f"perft {d} = {nodes}  time {t1-t0:.3f}s")
            continue
        if parts[0] == "go" and len(parts) == 3 and parts[1] == "depth":
            try:
                d = int(parts[2])
            except:
                print("bad depth")
                continue
            nodes_searched = 0
            t0 = time.time()
            val, best = alphabeta(board, d, -9999999, 9999999, white_to_move)
            t1 = time.time()
            if best is None:
                print("No legal moves available.")
            else:
                san = move_to_san(board, best)
                captured = make_move_on_board(board, best)
                print(f"Engine plays: {san}  (eval {val/100:.2f}) nodes {nodes_searched} time {t1-t0:.3f}s")
                # no auto-promotion handling
                white_to_move = not white_to_move
                show_board(board)
            continue

        # Otherwise it's a user move
        mv = parse_user_move(board, cmd, white_to_move)
        if mv is None:
            print("Illegal or ambiguous move.")
            continue
        r1,c1,r2,c2 = mv
        # final safety check: ensure piece color matches turn
        piece = board[r1][c1]
        if piece == '.':
            print("No piece on source.")
            continue
        if white_to_move and not piece.isupper():
            print("Illegal: it's White's turn.")
            continue
        if not white_to_move and not piece.islower():
            print("Illegal: it's Black's turn.")
            continue
        captured = make_move_on_board(board, mv)
        # if this leaves own king in check, undo
        if is_in_check(board, not white_to_move):  # after move, check the player who just moved? better check opponent attacking?
            # Actually we must check whether the side that just moved left themselves in check:
            # Since we updated board already, the side that moved is the opposite of white_to_move
            # We want to ensure their own king is not in check; that is is_in_check(board, side_that_just_moved)
            # side_that_just_moved = not white_to_move
            if is_in_check(board, not white_to_move):
                undo_move_on_board(board, mv, captured)
                print("Illegal move: king would be in check.")
                continue
        # Accept move
        white_to_move = not white_to_move
        show_board(board)

    print("Goodbye.")

if __name__ == "__main__":
    uci_loop()
