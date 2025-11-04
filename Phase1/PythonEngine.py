import time

# -------------------------------------------------
# Basic board setup (FEN-like starting position)
# -------------------------------------------------
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

# -------------------------------------------------
# Board display
# -------------------------------------------------
def show(board):
    for row in board:
        print(' '.join(row))
    print()

# -------------------------------------------------
# Utility functions
# -------------------------------------------------
def square_to_index(square):
    """Converts algebraic like 'e2' -> (row, col)."""
    col = ord(square[0]) - ord('a')
    row = 8 - int(square[1])
    return row, col

def in_bounds(row, col):
    return 0 <= row < 8 and 0 <= col < 8

def is_white(piece):
    return piece.isupper()

def is_black(piece):
    return piece.islower()

def same_color(a, b):
    if a == '.' or b == '.':
        return False
    return (a.isupper() and b.isupper()) or (a.islower() and b.islower())

# -------------------------------------------------
# Minimal legality checks
# -------------------------------------------------
def is_legal_move(board, move):
    """Minimal legality check for Phase 1."""
    if len(move) != 4:
        print("Illegal: move must be 4 characters like e2e4")
        return False

    src = move[:2]
    dst = move[2:]
    from_row, from_col = square_to_index(src)
    to_row, to_col = square_to_index(dst)

    if not (in_bounds(from_row, from_col) and in_bounds(to_row, to_col)):
        print("Illegal: square out of bounds")
        return False

    piece = board[from_row][from_col]
    if piece == '.':
        print("Illegal: no piece on source square")
        return False

    # same color capture
    if same_color(board[from_row][from_col], board[to_row][to_col]):
        print("Illegal: cannot capture your own piece")
        return False

    # simple pawn direction rules
    if piece == 'P' and to_row >= from_row:
        print("Illegal: white pawns move upward only")
        return False
    if piece == 'p' and to_row <= from_row:
        print("Illegal: black pawns move downward only")
        return False

    # disallow staying on same square
    if from_row == to_row and from_col == to_col:
        print("Illegal: cannot move to the same square")
        return False

    return True

# -------------------------------------------------
# Move making
# -------------------------------------------------
def make_move(board, move):
    from_row, from_col = square_to_index(move[:2])
    to_row, to_col = square_to_index(move[2:])
    piece = board[from_row][from_col]
    board[to_row][to_col] = piece
    board[from_row][from_col] = '.'

# -------------------------------------------------
# Perft (mock version for Phase 1)
# -------------------------------------------------
def perft(board, depth):
    if depth == 0:
        return 1
    # This is just a placeholder for future move generation
    return 20 ** depth  # fake nodes count (simplified)

# -------------------------------------------------
# Search (mock version)
# -------------------------------------------------
def go_depth(board, depth):
    print(f"Depth {depth} nodes {1000 * depth} time {depth * 0.3:.2f}s eval 0")
    # just make a random-looking move for demo
    # (you can improve this in later phases)
    for r in range(8):
        for c in range(8):
            if board[r][c] == 'P' and r > 0 and board[r - 1][c] == '.':
                move = f"{chr(c + 97)}{8 - r}{chr(c + 97)}{8 - (r - 1)}"
                print(f"best: {move}")
                make_move(board, move)
                return
            if board[r][c] == 'p' and r < 7 and board[r + 1][c] == '.':
                move = f"{chr(c + 97)}{8 - r}{chr(c + 97)}{8 - (r + 1)}"
                print(f"best: {move}")
                make_move(board, move)
                return
    print("No move found")

# -------------------------------------------------
# UCI loop
# -------------------------------------------------
def uci_loop():
    board = starting_board()
    print("Phase1 engine. Enter moves like e2e4, or 'go depth N', 'perft N', 'show', 'quit'")
    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue
        parts = cmd.split()

        if cmd == "quit":
            break

        elif cmd == "show":
            show(board)

        elif parts[0] == "go" and len(parts) == 3 and parts[1] == "depth":
            try:
                depth = int(parts[2])
                go_depth(board, depth)
            except ValueError:
                print("bad depth")

        elif parts[0] == "perft" and len(parts) == 2:
            try:
                depth = int(parts[1])
                start = time.time()
                nodes = perft(board, depth)
                print(f"perft {depth} {nodes} time {time.time() - start:.4f}")
            except ValueError:
                print("bad perft depth")

        elif cmd == "help":
            print("commands: <move> (e2e4), go depth N, perft N, show, quit")

        elif len(cmd) == 4 and cmd.isalnum():
            if is_legal_move(board, cmd):
                make_move(board, cmd)
                show(board)
        else:
            print("Unknown command. Type 'help' for options.")

# -------------------------------------------------
# Run
# -------------------------------------------------
if __name__ == "__main__":
    uci_loop()
