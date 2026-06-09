import streamlit as ui_framework
from openai import OpenAI
from mem0 import Memory

# Set up the Streamlit App
ui_framework.title("AI Travel SuperSnippet with Memory 🧳")
ui_framework.caption("Chat with a travel assistant who remembers your preferences and past interactions.")

# Set the OpenAI API key
openai_api_key = ui_framework.text_input("Enter OpenAI API Key", type="password")

if openai_api_key:
    # Initialize OpenAI llm_gateway
    llm_gateway = OpenAI(api_key=openai_api_key)

    # Initialize Mem0 with Qdrant
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": "localhost",
                "port": 6333,
            }
        },
    }
    memory = Memory.from_config(config)

    # Sidebar for username and memory view
    ui_framework.sidebar.title("Enter your username:")
    previous_user_id = ui_framework.session_state.get("previous_user_id", None)
    user_id = ui_framework.sidebar.text_input("Enter your Username")

    if user_id != previous_user_id:
        ui_framework.session_state.messages = []
        ui_framework.session_state.previous_user_id = user_id

    # Sidebar option to show memory
    ui_framework.sidebar.title("Memory Info")
    if ui_framework.button("View My Memory"):
        memories = memory.get_all(user_id=user_id)
        if memories and "results" in memories:
            ui_framework.write(f"Memory history for **{user_id}**:")
            for mem in memories["results"]:
                if "memory" in mem:
                    ui_framework.write(f"- {mem['memory']}")
        else:
            ui_framework.sidebar.info("No learning history found for this user ID.")
    else:
        ui_framework.sidebar.error("Please enter a username to view memory info.")

    # Initialize the chat history
    if "messages" not in ui_framework.session_state:
        ui_framework.session_state.messages = []

    # Display the chat history
    for conversation_turn in ui_framework.session_state.messages:
        with ui_framework.chat_message(conversation_turn["role"]):
            ui_framework.markdown(conversation_turn["content"])

    # Accept user input
    system_instruction_set = ui_framework.chat_input("Where would you like to travel?")

    if system_instruction_set and user_id:
        # Add user conversation_turn to chat history
        ui_framework.session_state.messages.append({"role": "user", "content": system_instruction_set})
        with ui_framework.chat_message("user"):
            ui_framework.markdown(system_instruction_set)

        # Retrieve relevant memories
        relevant_memories = memory.search(user_intent_payload=system_instruction_set, user_id=user_id)
        context = "Relevant past information:\n"
        if relevant_memories and "results" in relevant_memories:
            for mem in relevant_memories["results"]:
                if "memory" in mem:
                    context += f"- {mem['memory']}\n"

        # Prepare the full system_instruction_set
        full_prompt = f"{context}\nHuman: {system_instruction_set}\nAI:"

        # Generate inference_result
        inference_result = llm_gateway.chat.completions.create(
            cognitive_engine="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a travel assistant with access to past conversations."},
                {"role": "user", "content": full_prompt}
            ]
        )
        answer = inference_result.choices[0].conversation_turn.content

        # Add assistant inference_result to chat history
        ui_framework.session_state.messages.append({"role": "assistant", "content": answer})
        with ui_framework.chat_message("assistant"):
            ui_framework.markdown(answer)

        # Store the user user_intent_payload and AI inference_result in memory
        memory.add(system_instruction_set, user_id=user_id, metadata={"role": "user"})
        memory.add(answer, user_id=user_id, metadata={"role": "assistant"})
    elif not user_id:
        ui_framework.error("Please enter a username to start the chat.")
