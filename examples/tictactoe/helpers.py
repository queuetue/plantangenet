"""
TicTacToe game implementation using Plantangenet activities and tournament system.
"""
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from plantangenet.game import TurnBasedGameActivity, GameState
from plantangenet import GLOBAL_LOGGER

from examples.tictactoe.tictactoe_types import GameBoard, PlayerSymbol, GameState as TTTGameState
from examples.tictactoe.referee import TicTacToeReferee


def render_tictactoe_game_state(board, width=200, height=200, game=None, info_text=None):
    """Render a TicTacToe game state as a PIL Image."""
    from PIL import Image, ImageDraw, ImageFont

    # Create image with dark background
    img = Image.new('RGB', (width, height), color=(40, 60, 90))
    draw = ImageDraw.Draw(img)

    # Draw the TicTacToe board
    board_size = min(width, height) - 40
    board_x = (width - board_size) // 2
    board_y = (height - board_size) // 2 + 10

    cell_size = board_size // 3

    # Draw grid
    for i in range(4):
        x = board_x + i * cell_size
        y = board_y + i * cell_size
        draw.line([(x, board_y), (x, board_y + board_size)],
                  fill=(200, 200, 200), width=2)
        draw.line([(board_x, y), (board_x + board_size, y)],
                  fill=(200, 200, 200), width=2)

    # Draw X's and O's
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", cell_size // 2)
    except Exception:
        font = None

    for r in range(3):
        for c in range(3):
            cell_val = board.board[r][c]
            if cell_val != " ":
                x = board_x + c * cell_size + cell_size // 2
                y = board_y + r * cell_size + cell_size // 2
                color = (255, 100, 100) if cell_val == "X" else (100, 100, 255)
                if font:
                    bbox = draw.textbbox((0, 0), cell_val, font=font)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    draw.text((x - w//2, y - h//2), cell_val,
                              fill=color, font=font)
                else:
                    draw.text((x - 8, y - 8), cell_val, fill=color)

    # Draw game info
    if info_text is None:
        current_player = getattr(board, 'current_player', 'X')
        state = getattr(board, 'state', 'in_progress')
        winner = getattr(board, 'winner', None)
        if winner:
            info_text = f"Winner: {winner}"
        elif state == TTTGameState.FINISHED:
            info_text = "Draw"
        else:
            info_text = f"Current: {current_player}"

    draw.text((10, height-20), info_text, fill=(255, 255, 255))
    return img
