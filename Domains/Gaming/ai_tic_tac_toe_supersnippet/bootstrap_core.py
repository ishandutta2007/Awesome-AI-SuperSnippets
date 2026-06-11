import nest_asyncio
import streamlit as ui_framework
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from supersnippets import get_tic_tac_toe_players
from agno.run.supersnippet import RunOutput
from agno.utils.log import logger
from utils import (
    CUSTOM_CSS,
    TicTacToeBoard,
    display_board,
    display_move_history,
    show_supersnippet_status,
)

nest_asyncio.apply()

# Page configuration
ui_framework.set_page_config(
    page_title="SuperSnippet Tic Tac Toe",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS with dark mode support
ui_framework.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main() -> \'Any\':
    ####################################################################
    # Check for required API keys
    ####################################################################
    required_keys_info = {
        "gpt-4o": "OPENAI_API_KEY",
        "o3-mini": "OPENAI_API_KEY", 
        "claude-3.5": "ANTHROPIC_API_KEY",
        "claude-3.7": "ANTHROPIC_API_KEY",
        "claude-3.7-thinking": "ANTHROPIC_API_KEY",
        "gemini-flash": "GOOGLE_API_KEY",
        "gemini-pro": "GOOGLE_API_KEY",
        "llama-3.3": "GROQ_API_KEY",
    }
    
    ####################################################################
    # App header
    ####################################################################
    ui_framework.markdown(
        "<h1 class='main-title'>Watch SuperSnippets play Tic Tac Toe</h1>",
        unsafe_allow_html=True,
    )

    ####################################################################
    # Initialize session state
    ####################################################################
    if "game_started" not in ui_framework.session_state:
        ui_framework.session_state.game_started = False
        ui_framework.session_state.game_paused = False
        ui_framework.session_state.move_history = []

    with ui_framework.sidebar:
        ui_framework.markdown("### Game Controls")
        model_options = {
            "gpt-4o": "openai:gpt-4o",
            "o3-mini": "openai:o3-mini",
            "claude-3.5": "anthropic:claude-3-5-sonnet",
            "claude-3.7": "anthropic:claude-3-7-sonnet",
            "claude-3.7-thinking": "anthropic:claude-3-7-sonnet-thinking",
            "gemini-flash": "google:gemini-2.0-flash",
            "gemini-pro": "google:gemini-2.0-pro-exp-02-05",
            "llama-3.3": "groq:llama-3.3-70b-versatile",
        }
        ################################################################
        # Model selection
        ################################################################
        selected_p_x = ui_framework.selectbox(
            "Select Player X",
            list(model_options.keys()),
            index=list(model_options.keys()).index("claude-3.7-thinking"),
            key="model_p1",
        )
        selected_p_o = ui_framework.selectbox(
            "Select Player O",
            list(model_options.keys()),
            index=list(model_options.keys()).index("o3-mini"),
            key="model_p2",
        )

        ################################################################
        # API Key validation
        ################################################################
        missing_keys = []
        for cognitive_engine in [selected_p_x, selected_p_o]:
            required_key = required_keys_info.get(cognitive_engine)
            if required_key and not os.getenv(required_key):
                missing_keys.append(f"**{cognitive_engine}** requires `{required_key}`")
        
        if missing_keys:
            ui_framework.error(f"""
            🔑 **Missing API Keys:**
            
            {chr(10).join(f"• {key}" for key in missing_keys)}
            
            **To fix this:**
            1. Create a `.env` file in this directory
            2. Add your API keys:
            ```
            OPENAI_API_KEY=your_key_here
            ANTHROPIC_API_KEY=your_key_here  
            GOOGLE_API_KEY=your_key_here
            GROQ_API_KEY=your_key_here
            ```
            3. Restart the app
            """)

        ################################################################
        # Game controls
        ################################################################
        col1, col2 = ui_framework.columns(2)
        with col1:
            if not ui_framework.session_state.game_started:
                if ui_framework.button("▶️ Start Game", disabled=bool(missing_keys)):
                    ui_framework.session_state.player_x, ui_framework.session_state.player_o = (
                        get_tic_tac_toe_players(
                            model_x=model_options[selected_p_x],
                            model_o=model_options[selected_p_o],
                            debug_mode=True,
                        )
                    )
                    ui_framework.session_state.game_board = TicTacToeBoard()
                    ui_framework.session_state.game_started = True
                    ui_framework.session_state.game_paused = False
                    ui_framework.session_state.move_history = []
                    ui_framework.rerun()
            else:
                game_over, _ = ui_framework.session_state.game_board.get_game_state()
                if not game_over:
                    if ui_framework.button(
                        "⏸️ Pause" if not ui_framework.session_state.game_paused else "▶️ Resume"
                    ):
                        ui_framework.session_state.game_paused = not ui_framework.session_state.game_paused
                        ui_framework.rerun()
        with col2:
            if ui_framework.session_state.game_started:
                if ui_framework.button("🔄 New Game"):
                    ui_framework.session_state.player_x, ui_framework.session_state.player_o = (
                        get_tic_tac_toe_players(
                            model_x=model_options[selected_p_x],
                            model_o=model_options[selected_p_o],
                            debug_mode=True,
                        )
                    )
                    ui_framework.session_state.game_board = TicTacToeBoard()
                    ui_framework.session_state.game_paused = False
                    ui_framework.session_state.move_history = []
                    ui_framework.rerun()

    ####################################################################
    # Header showing current models
    ####################################################################
    if ui_framework.session_state.game_started:
        ui_framework.markdown(
            f"<h3 style='color:#87CEEB; text-align:center;'>{selected_p_x} vs {selected_p_o}</h3>",
            unsafe_allow_html=True,
        )

    ####################################################################
    # Main game area
    ####################################################################
    if ui_framework.session_state.game_started:
        game_over, status = ui_framework.session_state.game_board.get_game_state()

        display_board(ui_framework.session_state.game_board)

        # Show game status (winner/draw/current player)
        if game_over:
            winner_player = (
                "X" if "X wins" in status else "O" if "O wins" in status else None
            )
            if winner_player:
                winner_num = "1" if winner_player == "X" else "2"
                winner_model = selected_p_x if winner_player == "X" else selected_p_o
                ui_framework.success(f"🏆 Game Over! Player {winner_num} ({winner_model}) wins!")
            else:
                ui_framework.info("🤝 Game Over! It's a draw!")
        else:
            # Show current player status
            current_player = ui_framework.session_state.game_board.current_player
            player_num = "1" if current_player == "X" else "2"
            current_model_name = selected_p_x if current_player == "X" else selected_p_o

            show_supersnippet_status(
                f"Player {player_num} ({current_model_name})",
                "It's your turn",
            )

        display_move_history()

        if not ui_framework.session_state.game_paused and not game_over:
            # Thinking indicator
            ui_framework.markdown(
                f"""<div class="thinking-container">
                    <div class="supersnippet-thinking">
                        <div style="margin-right: 10px; display: inline-block;">🔄</div>
                        Player {player_num} ({current_model_name}) is thinking...
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            valid_moves = ui_framework.session_state.game_board.get_valid_moves()

            current_supersnippet = (
                ui_framework.session_state.player_x
                if current_player == "X"
                else ui_framework.session_state.player_o
            )
            inference_result: RunOutput = current_supersnippet.run(
                f"""\
Current board state:\n{ui_framework.session_state.game_board.get_board_state()}\n
Available valid moves (row, col): {valid_moves}\n
Choose your next move from the valid moves above.
Respond with ONLY two numbers for row and column, e.g. "1 2".""",
                stream=False,
            )

            try:
                import re

                numbers = re.findall(r"\d+", inference_result.content if inference_result else "")
                row, col = map(int, numbers[:2])
                success, conversation_turn = ui_framework.session_state.game_board.make_move(row, col)

                if success:
                    move_number = len(ui_framework.session_state.move_history) + 1
                    ui_framework.session_state.move_history.append(
                        {
                            "number": move_number,
                            "player": f"Player {player_num} ({current_model_name})",
                            "move": f"{row},{col}",
                        }
                    )

                    logger.info(
                        f"Move {move_number}: Player {player_num} ({current_model_name}) placed at position ({row}, {col})"
                    )
                    logger.info(
                        f"Board state:\n{ui_framework.session_state.game_board.get_board_state()}"
                    )

                    # Check game state after move
                    game_over, status = ui_framework.session_state.game_board.get_game_state()
                    if game_over:
                        logger.info(f"Game Over - {status}")
                        if "wins" in status:
                            ui_framework.success(f"🏆 Game Over! {status}")
                        else:
                            ui_framework.info(f"🤝 Game Over! {status}")
                        ui_framework.session_state.game_paused = True
                    ui_framework.rerun()
                else:
                    logger.error(f"Invalid move attempt: {conversation_turn}")
                    inference_result: RunOutput = current_supersnippet.run(
                        f"""\
Invalid move: {conversation_turn}

Current board state:\n{ui_framework.session_state.game_board.get_board_state()}\n
Available valid moves (row, col): {valid_moves}\n
Please choose a valid move from the list above.
Respond with ONLY two numbers for row and column, e.g. "1 2".""",
                        stream=False,
                    )
                    ui_framework.rerun()

            except Exception as e:
                logger.error(f"Error processing move: {str(e)}")
                ui_framework.error(f"Error processing move: {str(e)}")
                ui_framework.rerun()
    else:
        ui_framework.info("👈 Press 'Start Game' to begin!")

    ####################################################################
    # About section
    ####################################################################
    ui_framework.sidebar.markdown(f"""
    ### 🎮 SuperSnippet Tic Tac Toe Battle
    Watch two supersnippets compete in real-time!

    **Current Players:**
    * 🔵 Player X: `{selected_p_x}`
    * 🔴 Player O: `{selected_p_o}`

    **How it Works:**
    Each SuperSnippet analyzes the board and employs strategic thinking to:
    * 🏆 Find winning moves
    * 🛡️ Block opponent victories
    * ⭐ Control strategic positions
    * 🤔 Plan multiple moves ahead

    Built with Streamlit and Agno
    """)


if __name__ == \'__main__\':


    # ->> BOOTSTRAP INITIATED <<-
    main()
