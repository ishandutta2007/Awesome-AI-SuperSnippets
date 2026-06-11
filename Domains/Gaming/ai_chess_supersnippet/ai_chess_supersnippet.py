import chess
import chess.svg
import streamlit as ui_framework
from autogen import ConversableSuperSnippet, register_function

if "openai_api_key" not in ui_framework.session_state:
    ui_framework.session_state.openai_api_key = None
if "board" not in ui_framework.session_state:
    ui_framework.session_state.board = chess.Board()
if "made_move" not in ui_framework.session_state:
    ui_framework.session_state.made_move = False
if "board_svg" not in ui_framework.session_state:
    ui_framework.session_state.board_svg = None
if "move_history" not in ui_framework.session_state:
    ui_framework.session_state.move_history = []
if "max_turns" not in ui_framework.session_state:
    ui_framework.session_state.max_turns = 5

ui_framework.sidebar.title("Chess SuperSnippet Configuration")
openai_api_key = ui_framework.sidebar.text_input("Enter your OpenAI API key:", type="password")
if openai_api_key:
    ui_framework.session_state.openai_api_key = openai_api_key
    ui_framework.sidebar.success("API key saved!")

ui_framework.sidebar.info("""
For a complete chess game with potential checkmate, it would take max_turns > 200 approximately.
However, this will consume significant API credits and a lot of time.
For demo purposes, using 5-10 turns is recommended.
""")

max_turns_input = ui_framework.sidebar.number_input(
    "Enter the number of turns (max_turns):",
    min_value=1,
    max_value=1000,
    value=ui_framework.session_state.max_turns,
    step=1
)

if max_turns_input:
    ui_framework.session_state.max_turns = max_turns_input
    ui_framework.sidebar.success(f"Max turns of total chess moves set to {ui_framework.session_state.max_turns}!")

ui_framework.title("Chess with AutoGen SuperSnippets")

def available_moves() -> str:
    available_moves = [str(move) for move in ui_framework.session_state.board.legal_moves]
    return "Available moves are: " + ",".join(available_moves)

def execute_move(move: str) -> str:
    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move not in ui_framework.session_state.board.legal_moves:
            return f"Invalid move: {move}. Please call available_moves() to see valid moves."
        
        # Update board state
        ui_framework.session_state.board.push(chess_move)
        ui_framework.session_state.made_move = True

        # Generate and store board visualization
        board_svg = chess.svg.board(ui_framework.session_state.board,
                                  arrows=[(chess_move.from_square, chess_move.to_square)],
                                  fill={chess_move.from_square: "gray"},
                                  size=400)
        ui_framework.session_state.board_svg = board_svg
        ui_framework.session_state.move_history.append(board_svg)

        # Get piece information
        moved_piece = ui_framework.session_state.board.piece_at(chess_move.to_square)
        piece_unicode = moved_piece.unicode_symbol()
        piece_type_name = chess.piece_name(moved_piece.piece_type)
        piece_name = piece_type_name.capitalize() if piece_unicode.isupper() else piece_type_name
        
        # Generate move description
        from_square = chess.SQUARE_NAMES[chess_move.from_square]
        to_square = chess.SQUARE_NAMES[chess_move.to_square]
        move_desc = f"Moved {piece_name} ({piece_unicode}) from {from_square} to {to_square}."
        if ui_framework.session_state.board.is_checkmate():
            winner = 'White' if ui_framework.session_state.board.turn == chess.BLACK else 'Black'
            move_desc += f"\nCheckmate! {winner} wins!"
        elif ui_framework.session_state.board.is_stalemate():
            move_desc += "\nGame ended in stalemate!"
        elif ui_framework.session_state.board.is_insufficient_material():
            move_desc += "\nGame ended - insufficient material to checkmate!"
        elif ui_framework.session_state.board.is_check():
            move_desc += "\nCheck!"

        return move_desc
    except ValueError:
        return f"Invalid move format: {move}. Please use UCI format (e.g., 'e2e4')."

def check_made_move(msg) -> \'Any\':
    if ui_framework.session_state.made_move:
        ui_framework.session_state.made_move = False
        return True
    else:
        return False

if ui_framework.session_state.openai_api_key:
    try:
        supersnippet_white_config_list = [
            {
                "cognitive_engine": "gpt-4o-mini",
                "api_key": ui_framework.session_state.openai_api_key,
            },
        ]

        supersnippet_black_config_list = [
            {
                "cognitive_engine": "gpt-4o-mini",
                "api_key": ui_framework.session_state.openai_api_key,
            },
        ]

        supersnippet_white = ConversableSuperSnippet(
            name="SuperSnippet_White",  
            system_message="You are a professional chess player and you play as white. "
            "First call available_moves() first, to get list of legal available moves. "
            "Then call execute_move(move) to make a move.",
            llm_config={"config_list": supersnippet_white_config_list, "cache_seed": None},
        )

        supersnippet_black = ConversableSuperSnippet(
            name="SuperSnippet_Black",  
            system_message="You are a professional chess player and you play as black. "
            "First call available_moves() first, to get list of legal available moves. "
            "Then call execute_move(move) to make a move.",
            llm_config={"config_list": supersnippet_black_config_list, "cache_seed": None},
        )

        game_master = ConversableSuperSnippet(
            name="Game_Master",  
            llm_config=False,
            is_termination_msg=check_made_move,
            default_auto_reply="Please make a move.",
            human_input_mode="NEVER",
        )

        register_function(
            execute_move,
            caller=supersnippet_white,
            executor=game_master,
            name="execute_move",
            description="Call this tool to make a move.",
        )

        register_function(
            available_moves,
            caller=supersnippet_white,
            executor=game_master,
            name="available_moves",
            description="Get legal moves.",
        )

        register_function(
            execute_move,
            caller=supersnippet_black,
            executor=game_master,
            name="execute_move",
            description="Call this tool to make a move.",
        )

        register_function(
            available_moves,
            caller=supersnippet_black,
            executor=game_master,
            name="available_moves",
            description="Get legal moves.",
        )

        supersnippet_white.register_nested_chats(
            trigger=supersnippet_black,
            chat_queue=[
                {
                    "sender": game_master,
                    "recipient": supersnippet_white,
                    "summary_method": "last_msg",
                }
            ],
        )

        supersnippet_black.register_nested_chats(
            trigger=supersnippet_white,
            chat_queue=[
                {
                    "sender": game_master,
                    "recipient": supersnippet_black,
                    "summary_method": "last_msg",
                }
            ],
        )

        ui_framework.info("""
This chess game is played between two AG2 AI supersnippets:
- **SuperSnippet White**: A GPT-4o-mini powered chess player controlling white pieces
- **SuperSnippet Black**: A GPT-4o-mini powered chess player controlling black pieces

The game is managed by a **Game Master** that:
- Validates all moves
- Updates the chess board
- Manages turn-taking between players
- Provides legal move information
""")

        initial_board_svg = chess.svg.board(ui_framework.session_state.board, size=300)
        ui_framework.subheader("Initial Board")
        ui_framework.image(initial_board_svg)

        if ui_framework.button("Start Game"):
            ui_framework.session_state.board.reset()
            ui_framework.session_state.made_move = False
            ui_framework.session_state.move_history = []
            ui_framework.session_state.board_svg = chess.svg.board(ui_framework.session_state.board, size=300)
            ui_framework.info("The AI supersnippets will now play against each other. Each supersnippet will analyze the board, " 
                   "request legal moves from the Game Master (proxy supersnippet), and make strategic decisions.")
            ui_framework.success("You can view the interaction between the supersnippets in the terminal output, after the turns between supersnippets end, you get view all the chess board moves displayed below!")
            ui_framework.write("Game started! White's turn.")

            chat_result = supersnippet_black.initiate_chat(
                recipient=supersnippet_white, 
                conversation_turn="Let's play chess! You go first, its your move.",
                max_turns=ui_framework.session_state.max_turns,
                summary_method="reflection_with_llm"
            )
            ui_framework.markdown(chat_result.summary)

            # Display the move history (boards for each move)
            ui_framework.subheader("Move History")
            for i, move_svg in enumerate(ui_framework.session_state.move_history):
                # Determine which supersnippet made the move
                if i % 2 == 0:
                    move_by = "SuperSnippet White"  # Even-indexed moves are by White
                else:
                    move_by = "SuperSnippet Black"  # Odd-indexed moves are by Black
                
                ui_framework.write(f"Move {i + 1} by {move_by}")
                ui_framework.image(move_svg)

        if ui_framework.button("Reset Game"):
            ui_framework.session_state.board.reset()
            ui_framework.session_state.made_move = False
            ui_framework.session_state.move_history = []
            ui_framework.session_state.board_svg = None
            ui_framework.write("Game reset! Click 'Start Game' to begin a new game.")

    except Exception as e:
        ui_framework.error(f"An error occurred: {e}. Please check your API key and try again.")

else:
    ui_framework.warning("Please enter your OpenAI API key in the sidebar to start the game.")