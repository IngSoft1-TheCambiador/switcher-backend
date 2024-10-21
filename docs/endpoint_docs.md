# Endpoint documentation

For easier front/back integration we document the return type of the endpoints
used.



### Game state 

This endpoint provides an overview of the current game state, including details
about players, cards, the game board, and the game's overall configuration. It
returns a dictionary with the following keys:

- `initialized (bool)`: Indicates whether the game has been initialized.
- `player_ids (list[int])`: A list of unique player IDs currently in the game.
- `current_player (int)`: The ID of the player whose turn it currently is.
- `player_names (dict[int, str])`: A dictionary mapping each player's ID to their name.
- `player_colors (dict[int, str])`: A dictionary mapping each player's ID to their chosen color.
- `player_f_cards (dict[int, list[str]])`: A dictionary mapping each player's ID to a list of shape types that represent their figure cards (deck).
- `player_f_hand (dict[int, list[str]])`: A dictionary mapping each player's ID to a list of shape types that represent the figure cards currently in the player's hand.
- `player_m_cards (dict[int, list[str]])`: A dictionary mapping each player's ID to a list of move types that represent their move cards.
- `owner_id (int)`: The ID of the player who owns or created the game.
- `max_players (int)`: The maximum number of players allowed in the game.
- `min_players (int)`: The minimum number of players required to start the game.
- `name (str)`: The name of the game.
- `actual_board (str)`: The current state of the game board, represented as a string.
- `old_board (str)`: The previous state of the game board, represented as a string.
- `move_deck (list[str])`: A list of move types representing the deck of movement cards in the game.

Movement cards are strings of the form `movk`, figure cards are strings of the form `sk` (simple) or `hk` (hard), with $k \in \mathbb{N}$.
