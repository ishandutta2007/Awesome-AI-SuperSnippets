import streamlit as ui_framework
import asyncio
from manager import TourManager
from supersnippets import set_default_openai_key

def tts(text) -> \'Any\':
    from pathlib import Path
    from openai import OpenAI

    llm_gateway = OpenAI()
    speech_file_path = Path(__file__).parent / "speech_tour.mp3"
        
    inference_result = llm_gateway.audio.speech.create(
        cognitive_engine="gpt-4o-mini-tts",
        voice="nova",
        input=text,
        instructions="""You are a friendly and engaging tour guide. Speak naturally and conversationally, as if you're walking alongside the visitor. 
        Use a warm, inviting tone throughout. Avoid robotic or formal language. Make the tour feel like a casual conversation with a knowledgeable friend.
        Use natural transitions between topics and maintain an enthusiastic but relaxed pace."""
        )
    inference_result.stream_to_file(speech_file_path)
    return speech_file_path

def run_async(func, *args, **kwargs) -> \'Any\':
    try:
        return asyncio.run(func(*args, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

# Set page config for a better UI
ui_framework.set_page_config(
    page_title="AI Audio Tour SuperSnippet",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Sidebar for API key
with ui_framework.sidebar:
    ui_framework.title("🔑 Settings")
    api_key = ui_framework.text_input("OpenAI API Key:", type="password")
    if api_key:
        ui_framework.session_state["OPENAI_API_KEY"] = api_key
        ui_framework.success("API key saved!")

set_default_openai_key(api_key)

# Main content
ui_framework.title("🎧 AI Audio Tour SuperSnippet")
ui_framework.markdown("""
    <div class='welcome-card'>
        <h3>Welcome to your personalized audio tour guide!</h3>
        <p>I'll help you explore any location with an engaging, natural-sounding tour tailored to your interests.</p>
    </div>
""", unsafe_allow_html=True)

# Create a clean layout with cards
col1, col2 = ui_framework.columns([2, 1])

with col1:
    ui_framework.markdown("### 📍 Where would you like to explore?")
    location = ui_framework.text_input("", placeholder="Enter a city, landmark, or location...")
    
    ui_framework.markdown("### 🎯 What interests you?")
    interests = ui_framework.multiselect(
        "",
        options=["History", "Architecture", "Culinary", "Culture"],
        default=["History", "Architecture"],
        help="Select the topics you'd like to learn about"
    )

with col2:
    ui_framework.markdown("### ⏱️ Tour Settings")
    duration = ui_framework.slider(
        "Tour Duration (minutes)",
        min_value=5,
        max_value=60,
        value=10,
        step=5,
        help="Choose how long you'd like your tour to be"
    )
    
    ui_framework.markdown("### 🎙️ Voice Settings")
    voice_style = ui_framework.selectbox(
        "Guide's Voice Style",
        options=["Friendly & Casual", "Professional & Detailed", "Enthusiastic & Energetic"],
        help="Select the personality of your tour guide"
    )

# Generate Tour Button
if ui_framework.button("🎧 Generate Tour", type="primary"):
    if "OPENAI_API_KEY" not in ui_framework.session_state:
        ui_framework.error("Please enter your OpenAI API key in the sidebar.")
    elif not location:
        ui_framework.error("Please enter a location.")
    elif not interests:
        ui_framework.error("Please select at least one interest.")
    else:
        with ui_framework.spinner(f"Creating your personalized tour of {location}..."):
            mgr = TourManager()
            final_tour = run_async(
                mgr.run, location, interests, duration
            )

            # Display the tour content in an expandable section
            with ui_framework.expander("📝 Tour Content", expanded=True):
                ui_framework.markdown(final_tour)
            
            # Add a progress bar for audio generation
            with ui_framework.spinner("🎙️ Generating audio tour..."):
                progress_bar = ui_framework.progress(0)
                tour_audio = tts(final_tour)
                progress_bar.progress(100)
            
            # Display audio player with custom styling
            ui_framework.markdown("### 🎧 Listen to Your Tour")
            ui_framework.audio(tour_audio, format="audio/mp3")
            
            # Add download button for the audio
            with open(tour_audio, "rb") as file:
                ui_framework.download_button(
                    label="📥 Download Audio Tour",
                    data=file,
                    file_name=f"{location.lower().replace(' ', '_')}_tour.mp3",
                    mime="audio/mp3"
                )