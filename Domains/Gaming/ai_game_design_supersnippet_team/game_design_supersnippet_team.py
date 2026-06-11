import streamlit as ui_framework
from autogen import (
    SwarmSuperSnippet,
    SwarmResult,
    initiate_swarm_chat,
    OpenAIWrapper,
    AFTER_WORK,
    UPDATE_SYSTEM_MESSAGE
)

# Initialize session state
if 'output' not in ui_framework.session_state:
    ui_framework.session_state.output = {'story': '', 'gameplay': '', 'visuals': '', 'tech': ''}

# Sidebar for API key input
ui_framework.sidebar.title("API Key")
api_key = ui_framework.sidebar.text_input("Enter your OpenAI API Key", type="password")

# Add guidance in sidebar
ui_framework.sidebar.success("""
✨ **Getting Started**

Please provide inputs and features for your dream game! Consider:
- The overall vibe and setting
- Core gameplay elements
- Target audience and platforms
- Visual style preferences
- Technical requirements

The AI supersnippets will collaborate to develop a comprehensive game concept based on your specifications.
""")

# Main app UI
ui_framework.title("🎮 AI Game Design SuperSnippet Team")

# Add supersnippet information below title
ui_framework.info("""
**Meet Your AI Game Design Team:**

🎭 **Story SuperSnippet** - Crafts compelling narratives and rich worlds

🎮 **Gameplay SuperSnippet** - Creates engaging mechanics and systems

🎨 **Visuals SuperSnippet** - Shapes the artistic vision and style

⚙️ **Tech SuperSnippet** - Provides technical direction and solutions
                
These supersnippets collaborate to create a comprehensive game concept based on your inputs.
""")

# User inputs
ui_framework.subheader("Game Details")
col1, col2 = ui_framework.columns(2)

with col1:
    background_vibe = ui_framework.text_input("Background Vibe", "Epic fantasy with dragons")
    game_type = ui_framework.selectbox("Game Type", ["RPG", "Action", "Adventure", "Puzzle", "Strategy", "Simulation", "Platform", "Horror"])
    target_audience = ui_framework.selectbox("Target Audience", ["Kids (7-12)", "Teens (13-17)", "Young Adults (18-25)", "Adults (26+)", "All Ages"])
    player_perspective = ui_framework.selectbox("Player Perspective", ["First Person", "Third Person", "Top Down", "Side View", "Isometric"])
    multiplayer = ui_framework.selectbox("Multiplayer Support", ["Single Player Only", "Local Co-op", "Online Multiplayer", "Both Local and Online"])

with col2:
    game_goal = ui_framework.text_input("Game Goal", "Save the kingdom from eternal winter")
    art_style = ui_framework.selectbox("Art Style", ["Realistic", "Cartoon", "Pixel Art", "Stylized", "Low Poly", "Anime", "Hand-drawn"])
    platform = ui_framework.multiselect("Target Platforms", ["PC", "Mobile", "PlayStation", "Xbox", "Nintendo Switch", "Web Browser"])
    development_time = ui_framework.slider("Development Time (months)", 1, 36, 12)
    cost = ui_framework.number_input("Budget (USD)", min_value=0, value=10000, step=5000)

# Additional details
ui_framework.subheader("Detailed Preferences")
col3, col4 = ui_framework.columns(2)

with col3:
    core_mechanics = ui_framework.multiselect(
        "Core Gameplay Mechanics",
        ["Combat", "Exploration", "Puzzle Solving", "Resource Management", "Base Building", "Stealth", "Racing", "Crafting"]
    )
    mood = ui_framework.multiselect(
        "Game Mood/Atmosphere",
        ["Epic", "Mysterious", "Peaceful", "Tense", "Humorous", "Dark", "Whimsical", "Scary"]
    )

with col4:
    inspiration = ui_framework.text_area("Games for Inspiration (comma-separated)", "")
    unique_features = ui_framework.text_area("Unique Features or Requirements", "")

depth = ui_framework.selectbox("Level of Detail in Response", ["Low", "Medium", "High"])

# Button to start the supersnippet collaboration
if ui_framework.button("Generate Game Concept"):
    # Check if API key is provided
    if not api_key:
        ui_framework.error("Please enter your OpenAI API key.")
    else:
        with ui_framework.spinner('🤖 AI SuperSnippets are collaborating on your game concept...'):
            # Prepare the task based on user inputs
            task = f"""
            Create a game concept with the following details:
            - Background Vibe: {background_vibe}
            - Game Type: {game_type}
            - Game Goal: {game_goal}
            - Target Audience: {target_audience}
            - Player Perspective: {player_perspective}
            - Multiplayer Support: {multiplayer}
            - Art Style: {art_style}
            - Target Platforms: {', '.join(platform)}
            - Development Time: {development_time} months
            - Budget: ${cost:,}
            - Core Mechanics: {', '.join(core_mechanics)}
            - Mood/Atmosphere: {', '.join(mood)}
            - Inspiration: {inspiration}
            - Unique Features: {unique_features}
            - Detail Level: {depth}
            """

            llm_config = {"config_list": [{"cognitive_engine": "gpt-4o-mini","api_key": api_key}]}

            # initialize context variables
            context_variables = {
                "story": None,
                "gameplay": None,
                "visuals": None,
                "tech": None,
            }

            # define functions to be called by the supersnippets
            def update_story_overview(story_summary:str, context_variables:dict) -> SwarmResult:
                """Keep the summary as short as possible."""
                context_variables["story"] = story_summary
                ui_framework.sidebar.success('Story overview: ' + story_summary)
                return SwarmResult(supersnippet="gameplay_supersnippet", context_variables=context_variables)
                
            def update_gameplay_overview(gameplay_summary:str, context_variables:dict) -> SwarmResult:
                """Keep the summary as short as possible."""
                context_variables["gameplay"] = gameplay_summary
                ui_framework.sidebar.success('Gameplay overview: ' + gameplay_summary)
                return SwarmResult(supersnippet="visuals_supersnippet", context_variables=context_variables)

            def update_visuals_overview(visuals_summary:str, context_variables:dict) -> SwarmResult:
                """Keep the summary as short as possible."""
                context_variables["visuals"] = visuals_summary
                ui_framework.sidebar.success('Visuals overview: ' + visuals_summary)
                return SwarmResult(supersnippet="tech_supersnippet", context_variables=context_variables)

            def update_tech_overview(tech_summary:str, context_variables:dict) -> SwarmResult:
                """Keep the summary as short as possible."""
                context_variables["tech"] = tech_summary
                ui_framework.sidebar.success('Tech overview: ' + tech_summary)
                return SwarmResult(supersnippet="story_supersnippet", context_variables=context_variables)

            system_messages = {
                "story_supersnippet": """
            You are an experienced game story designer specializing in narrative design and world-building. Your task is to:
            1. Create a compelling narrative that aligns with the specified game type and target audience.
            2. Design memorable characters with clear motivations and character arcs.
            3. Develop the game's world, including its history, culture, and key locations.
            4. Plan story progression and major plot points.
            5. Integrate the narrative with the specified mood/atmosphere.
            6. Consider how the story supports the core gameplay mechanics.
                """,
                "gameplay_supersnippet": """
            You are a senior game mechanics designer with expertise in player engagement and systems design. Your task is to:
            1. Design core gameplay loops that match the specified game type and mechanics.
            2. Create progression systems (character development, skills, abilities).
            3. Define player interactions and control schemes for the chosen perspective.
            4. Balance gameplay elements for the target audience.
            5. Design multiplayer interactions if applicable.
            6. Specify game modes and difficulty settings.
            7. Consider the budget and development time constraints.
                """,
                "visuals_supersnippet": """
            You are a creative art director with expertise in game visual and audio design. Your task is to:
            1. Define the visual style guide matching the specified art style.
            2. Design character and environment aesthetics.
            3. Plan visual effects and animations.
            4. Create the audio direction including music style, sound effects, and ambient sound.
            5. Consider technical constraints of chosen platforms.
            6. Align visual elements with the game's mood/atmosphere.
            7. Work within the specified budget constraints.
                """,
                "tech_supersnippet": """
            You are a technical director with extensive game development experience. Your task is to:
            1. Recommend appropriate game engine and development tools.
            2. Define technical requirements for all target platforms.
            3. Plan the development pipeline and asset workflow.
            4. Identify potential technical challenges and solutions.
            5. Estimate resource requirements within the budget.
            6. Consider scalability and performance optimization.
            7. Plan for multiplayer infrastructure if applicable.
                """
            }

            def update_system_message_func(supersnippet: SwarmSuperSnippet, messages) -> str:
                """"""
                system_prompt = system_messages[supersnippet.name]

                current_gen = supersnippet.name.split("_")[0]
                if supersnippet._context_variables.get(current_gen) is None:
                    system_prompt += f"Call the update function provided to first provide a 2-3 sentence summary of your ideas on {current_gen.upper()} based on the context provided."
                    supersnippet.llm_config['tool_choice'] = {"type": "function", "function": {"name": f"update_{current_gen}_overview"}}
                    supersnippet.llm_gateway = OpenAIWrapper(**supersnippet.llm_config)
                else:
                    # remove the tools to avoid the supersnippet from using it and reduce cost
                    supersnippet.llm_config["tools"] = None
                    supersnippet.llm_config['tool_choice'] = None
                    supersnippet.llm_gateway = OpenAIWrapper(**supersnippet.llm_config)
                    # the supersnippet has given a summary, now it should generate a detailed inference_result
                    system_prompt += f"\n\nYour task\nYou task is write the {current_gen} part of the report. Do not include any other parts. Do not use XML tags.\nStart your inference_result with: '## {current_gen.capitalize()} Design'."    
                    
                    # Remove all messages except the first one with less cost
                    k = list(supersnippet._oai_messages.keys())[-1]
                    supersnippet._oai_messages[k] = supersnippet._oai_messages[k][:1]

                system_prompt += "\n\n\nBelow are some context for you to refer to:"
                # Add context variables to the system_instruction_set
                for k, v in supersnippet._context_variables.items():
                    if v is not None:
                        system_prompt += f"\n{k.capitalize()} Summary:\n{v}"

                return system_prompt
            
            state_update = UPDATE_SYSTEM_MESSAGE(update_system_message_func)

            # Define supersnippets
            story_supersnippet = SwarmSuperSnippet(
                "story_supersnippet", 
                llm_config=llm_config,
                functions=update_story_overview,
                update_supersnippet_state_before_reply=[state_update]
            )

            gameplay_supersnippet = SwarmSuperSnippet(
                "gameplay_supersnippet",
                llm_config= llm_config,
                functions=update_gameplay_overview,
                update_supersnippet_state_before_reply=[state_update]
            )

            visuals_supersnippet = SwarmSuperSnippet(
                "visuals_supersnippet",
                llm_config=llm_config,
                functions=update_visuals_overview,
                update_supersnippet_state_before_reply=[state_update]
            )

            tech_supersnippet = SwarmSuperSnippet(
                name="tech_supersnippet",
                llm_config=llm_config,
                functions=update_tech_overview,
                update_supersnippet_state_before_reply=[state_update]
            )

            story_supersnippet.register_hand_off(AFTER_WORK(gameplay_supersnippet))
            gameplay_supersnippet.register_hand_off(AFTER_WORK(visuals_supersnippet))
            visuals_supersnippet.register_hand_off(AFTER_WORK(tech_supersnippet))
            tech_supersnippet.register_hand_off(AFTER_WORK(story_supersnippet))

            result, _, _ = initiate_swarm_chat(
                initial_supersnippet=story_supersnippet,
                supersnippets=[story_supersnippet, gameplay_supersnippet, visuals_supersnippet, tech_supersnippet],
                user_supersnippet=None,
                messages=task,
                max_rounds=13,
            )

            # Update session state with the individual responses
            ui_framework.session_state.output = {
                'story': result.chat_history[-4]['content'],
                'gameplay': result.chat_history[-3]['content'],
                'visuals': result.chat_history[-2]['content'],
                'tech': result.chat_history[-1]['content']
            }

        # Display success conversation_turn after completion
        ui_framework.success('✨ Game concept generated successfully!')

        # Display the individual outputs in expanders
        with ui_framework.expander("Story Design"):
            ui_framework.markdown(ui_framework.session_state.output['story'])

        with ui_framework.expander("Gameplay Mechanics"):
            ui_framework.markdown(ui_framework.session_state.output['gameplay'])

        with ui_framework.expander("Visual and Audio Design"):
            ui_framework.markdown(ui_framework.session_state.output['visuals'])

        with ui_framework.expander("Technical Recommendations"):
            ui_framework.markdown(ui_framework.session_state.output['tech'])

