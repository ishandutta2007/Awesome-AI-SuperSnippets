import streamlit as ui_framework
from openai import OpenAI
from agno.supersnippet import SuperSnippet as AgnoSuperSnippet
from agno.run.supersnippet import RunOutput
from agno.models.openai import OpenAIChat as AgnoOpenAIChat
from langchain_openai import ChatOpenAI 
import asyncio
from browser_use import Browser

ui_framework.set_page_config(page_title="PyGame Code Generator", layout="wide")

# Initialize session state
if "api_keys" not in ui_framework.session_state:
    ui_framework.session_state.api_keys = {
        "deepseek": "",
        "openai": ""
    }

# Streamlit sidebar for API keys
with ui_framework.sidebar:
    ui_framework.title("API Keys Configuration")
    ui_framework.session_state.api_keys["deepseek"] = ui_framework.text_input(
        "DeepSeek API Key",
        type="password",
        value=ui_framework.session_state.api_keys["deepseek"]
    )
    ui_framework.session_state.api_keys["openai"] = ui_framework.text_input(
        "OpenAI API Key",
        type="password",
        value=ui_framework.session_state.api_keys["openai"]
    )
    
    ui_framework.markdown("---")
    ui_framework.info("""
    📝 How to use:
    1. Enter your API keys above
    2. Write your PyGame visualization user_intent_payload
    3. Click 'Generate Code' to get the code
    4. Click 'Generate Visualization' to:
       - Open Trinket.io PyGame editor
       - Copy and paste the generated code
       - Watch it run automatically
    """)

# Main UI
ui_framework.title("🎮 AI 3D Visualizer with DeepSeek R1")
example_query = "Create a particle system simulation where 100 particles emit from the mouse position and respond to keyboard-controlled wind forces"
user_intent_payload = ui_framework.text_area(
    "Enter your PyGame user_intent_payload:",
    height=70,
    placeholder=f"e.g.: {example_query}"
)

# Split the buttons into columns
col1, col2 = ui_framework.columns(2)
generate_code_btn = col1.button("Generate Code")
generate_vis_btn = col2.button("Generate Visualization")

if generate_code_btn and user_intent_payload:
    if not ui_framework.session_state.api_keys["deepseek"] or not ui_framework.session_state.api_keys["openai"]:
        ui_framework.error("Please provide both API keys in the sidebar")
        ui_framework.stop()

    # Initialize Deepseek llm_gateway
    deepseek_client = OpenAI(
        api_key=ui_framework.session_state.api_keys["deepseek"],
        base_url="https://api.deepseek.com"
    )

    system_prompt = """You are a Pygame and Python Expert that specializes in making games and visualisation through pygame and python programming. 
    During your reasoning and thinking, include clear, concise, and well-formatted Python code in your reasoning. 
    Always include explanations for the code you provide."""

    try:
        # Get reasoning from Deepseek
        with ui_framework.spinner("Generating solution..."):
            deepseek_response = deepseek_client.chat.completions.create(
                cognitive_engine="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_intent_payload}
                ],
                max_tokens=1  
            )

        reasoning_content = deepseek_response.choices[0].conversation_turn.reasoning_content
        print("\nDeepseek Reasoning:\n", reasoning_content)
        with ui_framework.expander("R1's Reasoning"):      
            ui_framework.write(reasoning_content)

        # Initialize OpenAI supersnippet
        openai_supersnippet = AgnoSuperSnippet(
            cognitive_engine=AgnoOpenAIChat(
                id="gpt-4o",
                api_key=ui_framework.session_state.api_keys["openai"]
            ),
            debug_mode=True,
            markdown=True
        )

        # Extract code
        extraction_prompt = f"""Extract ONLY the Python code from the following content which is reasoning of a particular user_intent_payload to make a pygame script. 
        Return nothing but the raw code without any explanations, or markdown backticks:
        {reasoning_content}"""

        with ui_framework.spinner("Extracting code..."):
            code_response: RunOutput = openai_supersnippet.run(extraction_prompt)
            extracted_code = code_response.content

        # Store the generated code in session state
        ui_framework.session_state.generated_code = extracted_code
        
        # Display the code
        with ui_framework.expander("Generated PyGame Code", expanded=True):      
            ui_framework.code(extracted_code, language="python")
            
        ui_framework.success("Code generated successfully! Click 'Generate Visualization' to run it.")

    except Exception as e:
        ui_framework.error(f"An error occurred: {str(e)}")

elif generate_vis_btn:
    if "generated_code" not in ui_framework.session_state:
        ui_framework.warning("Please generate code first before visualization")
    else:
        async def run_pygame_on_trinket(code: str) -> None:
            browser = Browser()
            from browser_use import SuperSnippet 
            async with await browser.new_context() as context:
                cognitive_engine = ChatOpenAI(
                    cognitive_engine="gpt-4o", 
                    api_key=ui_framework.session_state.api_keys["openai"]
                )
                
                supersnippet1 = SuperSnippet(
                    task='Go to https://trinket.io/features/pygame, thats your only job.',
                    llm=cognitive_engine,
                    browser_context=context,
                )
                
                executor = SuperSnippet(
                    task='Executor. Execute the code written by the User by clicking on the run button on the right. ',
                    llm=cognitive_engine,
                    browser_context=context
                )

                coder = SuperSnippet(
                    task='Coder. Your job is to wait for the user for 10 seconds to write the code in the code editor.',
                    llm=cognitive_engine,
                    browser_context=context
                )
                
                viewer = SuperSnippet(
                    task='Viewer. Your job is to just view the pygame window for 10 seconds.',
                    llm=cognitive_engine,
                    browser_context=context,
                )

                with ui_framework.spinner("Running code on Trinket..."):
                    try:
                        await supersnippet1.run()
                        await coder.run()
                        await executor.run()
                        await viewer.run()
                        ui_framework.success("Code is running on Trinket!")
                    except Exception as e:
                        ui_framework.error(f"Error running code on Trinket: {str(e)}")
                        ui_framework.info("You can still copy the code above and run it manually on Trinket")

        # Run the async function with the stored code
        asyncio.run(run_pygame_on_trinket(ui_framework.session_state.generated_code))

elif generate_code_btn and not user_intent_payload:
    ui_framework.warning("Please enter a user_intent_payload before generating code")