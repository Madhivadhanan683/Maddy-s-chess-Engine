import time
import copy

# -----------------------------------------------------
# Board Setup
# -----------------------------------------------------
def starting_board():
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR")
    ]

def show(board):
    print("\n   a b c d e f g h")
    for r in range(8):
        print(f"{8 - r}  {' '.join(board[r])}  {8 - r}")
    print("   a b c d e f g h\n")

def square_to_index(sq):
    col = ord(sq[0]) - ord('a')
    row = 8 - int(sq[1])
    return row, col

def index_to_square(r, c):
    return chr(c + ord('a')) + str(8 - r)

# -----------------------------------------------------
# Move Parsing
# -----------------------------------------------------
def parse_move(board, move_str, white_to_move):
    move_str = move_str.strip()
    # coordinate notation (e2e4)
    if len(move_str) == 4 and move_str[0] in "abcdefgh" and move_str[2] in "abcdefgh":
        return square_to_index(move_str[:2]) + square_to_index(move_str[2:])

    # Castling
    if move_str in ["O-O", "o-o", "0-0"]:
        return (7, 4, 7, 6) if white_to_move else (0, 4, 0, 6)
    if move_str in ["O-O-O", "o-o-o", "0-0-0"]:
        return (7, 4, 7, 2) if white_to_move else (0, 4, 0, 2)

    # Determine color and piece
    piece_letter = "P"
    is_white_piece = white_to_move

    # Check first character for piece or pawn
    first = move_str[0]
    if first in "NBRQK" or first in "nbrqk":
        piece_letter = first.upper()
        is_white_piece = first.isupper()
        move_str = move_str[1:]
    else:
        piece_letter = "P"
        is_white_piece = white_to_move

    # Destination square (last two)
    dest = move_str[-2:]
    if dest[0] not in "abcdefgh" or dest[1] not in "12345678":
        return None
    to_row, to_col = square_to_index(dest)

    move_str = move_str.replace("x", "")

    # Find matching piece
    candidates = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == '.':
                continue
            if is_white_piece and piece.isupper() and piece.upper() == piece_letter:
                if is_pseudo_legal(board, r, c, to_row, to_col):
                    candidates.append((r, c))
            if not is_white_piece and piece.islower() and piece.lower() == piece_letter.lower():
                if is_pseudo_legal(board, r, c, to_row, to_col):
                    candidates.append((r, c))
    if not candidates:
        return None
    return (*candidates[0], to_row, to_col)

# -----------------------------------------------------
# Move Legality
# -----------------------------------------------------
def is_pseudo_legal(board, r1, c1, r2, c2):
    piece = board[r1][c1]
    if piece == '.':
        return False
    color = piece.isupper()
    dr, dc = r2 - r1, c2 - c1

    target = board[r2][c2]
    if target != '.':
        if target.isupper() == piece.isupper():
            return False

    p = piece.upper()
    if p == 'P':
        direction = -1 if color else 1
        start_row = 6 if color else 1
        if dc == 0 and board[r2][c2] == '.':
            if dr == direction:
                return True
            if dr == 2 * direction and r1 == start_row and board[r1 + direction][c1] == '.':
                return True
        if abs(dc) == 1 and dr == direction and board[r2][c2] != '.':
            return True
    elif p == 'N':
        return (abs(dr), abs(dc)) in [(1, 2), (2, 1)]
    elif p == 'B':
        if abs(dr) != abs(dc): return False
        return clear_path(board, r1, c1, r2, c2)
    elif p == 'R':
        if dr != 0 and dc != 0: return False
        return clear_path(board, r1, c1, r2, c2)
    elif p == 'Q':
        if abs(dr) == abs(dc) or dr == 0 or dc == 0:
            return clear_path(board, r1, c1, r2, c2)
    elif p == 'K':
        return max(abs(dr), abs(dc)) == 1
    return False

def clear_path(board, r1, c1, r2, c2):
    dr = (r2 - r1) and ((r2 - r1)//abs(r2 - r1))
    dc = (c2 - c1) and ((c2 - c1)//abs(c2 - c1))
    r, c = r1 + dr, c1 + dc
    while (r, c) != (r2, c2):
        if board[r][c] != '.':
            return False
        r += dr; c += dc
    return True

# -----------------------------------------------------
# Move Execution
# -----------------------------------------------------
def make_move(board, move_str, white_to_move):
    parsed = parse_move(board, move_str, white_to_move)
    if not parsed:
        print("Illegal or unrecognized move format.")
        return False
    r1, c1, r2, c2 = parsed
    if not is_pseudo_legal(board, r1, c1, r2, c2):
        print("Illegal move geometry.")
        return False
    piece = board[r1][c1]
    if white_to_move and not piece.isupper():
        print("Illegal: it's White's turn.")
        return False
    if not white_to_move and not piece.islower():
        print("Illegal: it's Black's turn.")
        return False
    board[r2][c2] = piece
    board[r1][c1] = '.'
    return True

# -----------------------------------------------------
# Simple Evaluation and Minimax
# -----------------------------------------------------
piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def evaluate(board):
    score = 0
    for row in board:
        for p in row:
            if p == '.': continue
            val = piece_values[p.upper()]
            score += val if p.isupper() else -val
    return score

def generate_moves(board, white_to_move):
    moves = []
    for r1 in range(8):
        for c1 in range(8):
            piece = board[r1][c1]
            if piece == '.': continue
            if white_to_move and not piece.isupper(): continue
            if not white_to_move and not piece.islower(): continue
            for r2 in range(8):
                for c2 in range(8):
                    if is_pseudo_legal(board, r1, c1, r2, c2):
                        moves.append((r1, c1, r2, c2))
    return moves

def minimax(board, depth, white_to_move):
    if depth == 0:
        return evaluate(board), None
    moves = generate_moves(board, white_to_move)
    if not moves:
        return evaluate(board), None
    best_move = None
    best_val = -9999 if white_to_move else 9999
    for m in moves:
        new_board = copy.deepcopy(board)
        r1, c1, r2, c2 = m
        new_board[r2][c2] = new_board[r1][c1]
        new_board[r1][c1] = '.'
        val, _ = minimax(new_board, depth - 1, not white_to_move)
        if white_to_move and val > best_val:
            best_val = val; best_move = m
        if not white_to_move and val < best_val:
            best_val = val; best_move = m
    return best_val, best_move

def go_depth(board, depth, white_to_move):
    val, move = minimax(board, depth, white_to_move)
    if not move:
        print("No moves found.")
        return
    r1, c1, r2, c2 = move
    algebraic = index_to_square(r1, c1) + index_to_square(r2, c2)
    print(f"Best move: {algebraic} (eval {val})")
    board[r2][c2] = board[r1][c1]
    board[r1][c1] = '.'

# -----------------------------------------------------
# Perft
# -----------------------------------------------------
def perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for m in generate_moves(board, True):
        new_board = copy.deepcopy(board)
        r1, c1, r2, c2 = m
        new_board[r2][c2] = new_board[r1][c1]
        new_board[r1][c1] = '.'
        nodes += perft(new_board, depth - 1)
    return nodes

# -----------------------------------------------------
# UCI Loop
# -----------------------------------------------------
def uci_loop():
    board = starting_board()
    white_to_move = True
    print("SimpleChess Engine Phase 1.4 — type e4, Nf3, nf6, go depth N, perft N, show, quit")
    show(board)

    while True:
        side = "White" if white_to_move else "Black"
        cmd = input(f"[{side}] > ").strip()
        if not cmd: continue
        parts = cmd.split()

        if cmd == "quit":
            break
        elif cmd == "show":
            show(board)
        elif parts[0] == "go" and len(parts) == 3 and parts[1] == "depth":
            depth = int(parts[2])
            go_depth(board, depth, white_to_move)
            white_to_move = not white_to_move
            show(board)
        elif parts[0] == "perft" and len(parts) == 2:
            depth = int(parts[1])
            start = time.time()
            print(f"Nodes: {perft(board, depth)}  Time: {time.time() - start:.3f}s")
        else:
            if make_move(board, cmd, white_to_move):
                white_to_move = not white_to_move
                show(board)

# -----------------------------------------------------
# Run
# -----------------------------------------------------
if __name__ == "__main__":
    uci_loop()
