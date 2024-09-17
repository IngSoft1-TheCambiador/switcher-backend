# Entities docs 

This document specifies the classes which inherit from the `pony.orm` entities
and its methods. 

> **Nota**: The `PrimaryKey` (ID) of all entities is automatically set and 
hence should not be modified by programmers nor users. Good practice calls for
setting the ID attribute to be private (which in Python means naming it with an
initial underscore (`_id`)) and using a getter function to access it. This 
explains the `get_id(self)` function in all classes.

### Game entitiy 

The `Game` entity represents a Switcher game (partida). 


Its methods are:

- `get_id(self)` : Returns the `PrimaryKey` (an ID of type `int`) of this object.
- `add_player(self, player_id : int)` : Adds a `Player` to this `Game`.
- `delete_player(self, player_id : int)`: Removes a `Player` from this game.
- `start(self)`: Starts this `Game`.
- `init_board(self)`: Randomly initializes the `Game` board.

### Player entity

A `Player` is an agent in the server which may join and participate in games. The methods of the `Player` class are: 


- `get_id(self)` : Returns the `PrimaryKey` (an ID of type `int`) of this object.
- `assign_fig_cards(self, n : int)`: Randomly assigns `n` figure cards to this
  player.
- `assign_mov_cards(self, n : int)`: Randomly assigns `n` movement cards to 
this player.

### Move entity 

A `Move` entity represents a movement card and specifies a move type (or rule). Its 
methods are 

- `...`

### Shape entity 

A `Shape` entity represents a figure card. Its methods are: 

- `...`
