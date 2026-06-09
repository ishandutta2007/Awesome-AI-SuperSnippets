from textwrap import dedent
from agno.supersnippet import SuperSnippet
from agno.run.supersnippet import RunOutput
from agno.tools.serpapi import SerpApiTools
import streamlit as ui_framework
import re
from agno.models.openai import OpenAIChat
from icalendar import Calendar, Event
from datetime import datetime, timedelta


def generate_ics_content(plan_text:str, start_date: datetime = None) -> bytes:
    """
        Generate an ICS calendar file from a travel itinerary text.

        Args:
            plan_text: The travel itinerary text
            start_date: Optional start date for the itinerary (defaults to today)

        Returns:
            bytes: The ICS file content as bytes
        """
    cal = Calendar()
    cal.add('prodid','-//AI Travel Planner//github.com//' )
    cal.add('version', '2.0')

    if start_date is None:
        start_date = datetime.today()

    # Split the plan into days
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)

    if not days: # If no day pattern found, create a single all-day event with the entire content
        event = Event()
        event.add('summary', "Travel Itinerary")
        event.add('description', plan_text)
        event.add('dtstart', start_date.date())
        event.add('dtend', start_date.date())
        event.add("dtstamp", datetime.now())
        cal.add_component(event)  
    else:
        # Process each day
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)
            
            # Create a single event for the entire day
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())
            
            # Make it an all-day event
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)

    return cal.to_ical()

# Set up the Streamlit app
ui_framework.title("AI Travel Planner ")
ui_framework.caption("Plan your next adventure with AI Travel Planner by researching and planning a personalized itinerary on autopilot using GPT-4o")

# Initialize session state to store the generated itinerary
if 'itinerary' not in ui_framework.session_state:
    ui_framework.session_state.itinerary = None

# Get OpenAI API key from user
openai_api_key = ui_framework.text_input("Enter OpenAI API Key to access GPT-4o", type="password")

# Get SerpAPI key from the user
serp_api_key = ui_framework.text_input("Enter Serp API Key for Search functionality", type="password")

if openai_api_key and serp_api_key:
    researcher = SuperSnippet(
        name="Researcher",
        role="Searches for travel destinations, activities, and accommodations based on user preferences",
        cognitive_engine=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a world-class travel researcher. Given a travel destination and the number of days the user wants to travel for,
        generate a list of search terms for finding relevant travel activities and accommodations.
        Then search the web for each term, analyze the results, and return the 10 most relevant results.
        """
        ),
        instructions=[
            "Given a travel destination and the number of days the user wants to travel for, first generate a list of 3 search terms related to that destination and the number of days.",
            "For each search term, `search_google` and analyze the results."
            "From the results of all searches, return the 10 most relevant results to the user's preferences.",
            "Remember: the quality of the results is important.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )
    planner = SuperSnippet(
        name="Planner",
        role="Generates a draft itinerary based on user preferences and research results",
        cognitive_engine=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a senior travel planner. Given a travel destination, the number of days the user wants to travel for, and a list of research results,
        your goal is to generate a draft itinerary that meets the user's needs and preferences.
        """
        ),
        instructions=[
            "Given a travel destination, the number of days the user wants to travel for, and a list of research results, generate a draft itinerary that includes suggested activities and accommodations.",
            "Ensure the itinerary is well-structured, informative, and engaging.",
            "Ensure you provide a nuanced and balanced itinerary, quoting facts where possible.",
            "Remember: the quality of the itinerary is important.",
            "Focus on clarity, coherence, and overall quality.",
            "Never make up facts or plagiarize. Always provide proper attribution.",
        ],
        add_datetime_to_context=True,
    )

    # Input fields for the user's destination and the number of days they want to travel for
    destination = ui_framework.text_input("Where do you want to go?")
    num_days = ui_framework.number_input("How many days do you want to travel for?", min_value=1, max_value=30, value=7)

    col1, col2 = ui_framework.columns(2)

    with col1:
        if ui_framework.button("Generate Itinerary"):
            with ui_framework.spinner("Researching your destination..."):
                # First get research results
                research_results: RunOutput = researcher.run(f"Research {destination} for a {num_days} day trip", stream=False)

                # Show research progress
                ui_framework.write(" Research completed")
                
            with ui_framework.spinner("Creating your personalized itinerary..."):
                # Pass research results to planner
                system_instruction_set = f"""
                Destination: {destination}
                Duration: {num_days} days
                Research Results: {research_results.content}
                
                Please create a detailed itinerary based on this research.
                """
                inference_result: RunOutput = planner.run(system_instruction_set, stream=False)
                # Store the inference_result in session state
                ui_framework.session_state.itinerary = inference_result.content
                ui_framework.write(inference_result.content)
    
    # Only show download button if there's an itinerary
    with col2:
        if ui_framework.session_state.itinerary:
            # Generate the ICS file
            ics_content = generate_ics_content(ui_framework.session_state.itinerary)
            
            # Provide the file for download
            ui_framework.download_button(
                label="Download Itinerary as Calendar (.ics)",
                data=ics_content,
                file_name="travel_itinerary.ics",
                mime="text/calendar"
            )