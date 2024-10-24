from constants import FAILURE, STATUS, SUCCESS
from board_shapes import shapes_on_board
from orm import Game

def is_valid_figure(board: str, fig: str, x: int, y: int):

    λ = shapes_on_board(board)
    λ = [b for b in λ if b.shape_code == fig]

    if len(λ) == 0:
        return {"message": f"The figure {fig} is not in the current board.",
                STATUS: FAILURE}

    if all( [ β.board[x][y] == 0 for β in λ] ):
        msg = f"""Figure {fig} exists in board, but not at ({x}, {y})"""
        return {"message": msg, STATUS: FAILURE}

    return {"message": "Success", STATUS: SUCCESS}



def make_partial_moves_effective(game: Game, used_movs: str, player_id: int):

    used_movs = used_movs.split(",")
    game.retrieve_player_move_cards(player_id, used_movs)
    game.commit_board()
