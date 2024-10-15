import numpy as np
from random import shuffle
from skimage.measure import label, regionprops

BOARD_SIZE = 6

def print_board(board):
    """Print the 6x6 board."""
    for row in board.reshape(BOARD_SIZE, BOARD_SIZE):
        print(row)

def board_to_matrix(board):
    """Reshape the flat board into a 2D array."""
    return board.reshape(BOARD_SIZE, BOARD_SIZE)

# This is simply practical for testing things out
def gen_board():
    """Generate and shuffle the default game board."""
    DEFAULT_BOARD = "r" * 9 + "b" * 9 + "g" * 9 + "y" * 9
    board = list(DEFAULT_BOARD)
    shuffle(board)
    letters_to_nums = {"r": 1, "b": 2, "g": 3, "y": 4}
    return np.array([letters_to_nums[x] for x in board])

def rotate_figure(figure):
    """Generate 4 rotations (90 degrees at a time) of the figure."""
    return [np.rot90(np.array(figure), k) for k in range(4)]

def get_unique_figures(figures):
    """Get unique figures by rotating and removing duplicates."""
    all_rotations = []
    for figure in figures:
        all_rotations.extend(rotate_figure(figure))
    unique_figures = list({tuple(map(tuple, fig)) for fig in all_rotations})
    return [np.array(fig) for fig in unique_figures]

def extract_figures(labeled_board):
    # Each connected component (CC) in the labeled board has the properties: 
    # bbox (bounding box) 
    # slice (the slice that isolates the CC)
    # label (the label of the CC)
    # Reference: https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_regionprops.html
    figs = []
    for prop in regionprops(labeled_board):
        # Is the slice isolating the CC of the same label than the CC?
        λ = labeled_board[prop.slice] == prop.label
        β = (prop.bbox[0], prop.bbox[1])
        figs.append( (λ.astype(int), β ))

    return figs


def filter_matching_figures(figures_with_positions, unique_figures):
    """Filter figures to only include those that match the unique figures."""
    return [
        (fig, position) for fig, position in figures_with_positions
        if any(np.array_equal(fig, unique) for unique in unique_figures)
    ]

def detect_board_figures(board):
    # Define all figures
    figures = {
        "h1": [[1, 0, 0], [1, 1, 1], [1, 0, 0]],  #  
        "h2": [[1, 1, 0, 0], [0, 1, 1, 1]],        # 
        "h3": [[0, 0, 1, 1], [1, 1, 1, 0]],        # 
        "h4": [[1, 0, 0], [1, 1, 0], [0, 1, 1]],   # 
        "h5": [[1, 1, 1, 1, 1]],                   # 
        "h6": [[1, 0, 0], [1, 0, 0], [1, 1, 1]],   # 
        "h7": [[1, 1, 1, 1], [0, 0, 0, 1]],        # 
        "h8": [[0, 0, 0, 1], [1, 1, 1, 1]],        # 
        "h9": [[0, 0, 1], [1, 1, 1], [0, 1, 0]],   # 
        "h10": [[0, 0, 1], [1, 1, 1], [1, 0, 0]],   # 
        "h11": [[1, 0, 0], [1, 1, 1], [0, 1, 0]],   # 
        "h12": [[1, 0, 0], [1, 1, 1], [0, 0, 1]],   # 
        "h13": [[1, 1, 1, 1], [0, 0, 1, 0]],        # 
        "h14": [[0, 0, 1, 0], [1, 1, 1, 1]],        # 
        "h15": [[0, 1, 1], [1, 1, 1]],              # 
        "h16": [[1, 0, 1], [1, 1, 1]],              # 
        "h17": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],   # 
        "h18": [[1, 1, 1], [0, 1, 1]],              # 
        "e1": [[0, 1, 1], [1, 1, 0]],              # 
        "e2": [[1, 1], [1, 1]],                    # 
        "e3": [[1, 1, 0], [0, 1, 1]],              # 
        "e4": [[0, 1, 0], [1, 1, 1]],              # 
        "e5": [[1, 1, 1], [0, 0, 1]],              # 
        "e6": [[1, 1, 1, 1]],                      # 
        "e7": [[0, 0, 1], [1, 1, 1]]               # 
    }

    # Generate unique rotated figures
    unique_figures = get_unique_figures(figures)
    board = board_to_matrix(board)


    # Label connected regions of an integer array.
    # Two pixels are connected when they are neighbors and have the same value.
    # In 2D, they can be neighbors either in a 1- or 2-connected sense.
    # The value refers to the maximum number of orthogonal hops to consider a
    # pixel/voxel a neighbor.
    labeled_board = label(board, connectivity=1)

    # Extract figures and positions
    figures_with_positions = extract_figures(labeled_board)

    # Filter matching figures
    good_ones = filter_matching_figures(figures_with_positions, unique_figures)

    return good_ones


def construct_6x6_matrix(figure, position):
    """
    Create a 6x6 boolean matrix with the figure placed at the correct position.
    """
    matrix = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
    top_left_row, top_left_col = position
    fig_rows, fig_cols = figure.shape
    
    # Place the figure in the matrix at the correct position
    matrix[top_left_row:top_left_row + fig_rows, top_left_col:top_left_col + fig_cols] = figure
    
    return matrix

# Run this code if you want to see, step by step, what the algorithms 
# are doing.
#
# board = gen_board()
# reshaped = board_to_matrix(board)
# labeled = label(reshaped, connectivity = 1)
# figs = extract_figures(labeled)
# print("Initial board : \n", board)
# print("\nBoard as matrix: \n", reshaped)
# print("\nConnected components (labeled board): \n", labeled)
# print("\nExtracted figures: \n", figs)
# 
# print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
# res = detect_board_figures(board)
# print_board(board)
# for x in res:
#     print("\nFIG : \n", x[0])
#     print("POS : ", x[1])
# 
# # Construct 6x6 matrices for each matching figure
# matching_6x6_matrices = [
#     construct_6x6_matrix(fig, position) for fig, position in res
# ]
#
# for m in matching_6x6_matrices:
#     print("\n", m)
