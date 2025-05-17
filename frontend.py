import streamlit as st
import requests
from typing import List, Dict
import time

st.set_page_config(page_title="Agentic RAG Chat", page_icon="🤖", layout="centered")
st.title("🤖 Agentic RAG Chatbot")

API_URL = "http://localhost:8001/query"  # Updated to match the correct port

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # List of dicts: {"role": "user"|"assistant", "content": str, "metadata": dict}

def format_metadata_value(value):
    """Format metadata values appropriately based on type."""
    if isinstance(value, float):
        return f"{value:.3f}"  # Show 3 decimal places for floats
    elif isinstance(value, bool):
        return "Yes" if value else "No"
    else:
        return str(value)

def chat(query: str) -> Dict:
    """Send a query to the API and return the response with timing information."""
    start_time = time.time()
    try:
        response = requests.post(API_URL, json={"text": query}, timeout=30)
        
        # Calculate actual processing time regardless of API response
        actual_processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Ensure metadata exists
            if "metadata" not in result:
                result["metadata"] = {}
                
            # Add actual processing time if not provided by API
            if "processing_time" not in result["metadata"] or result["metadata"]["processing_time"] == 0:
                result["metadata"]["processing_time"] = actual_processing_time
                
            # Add default confidence if not provided
            if "confidence" not in result["metadata"] or result["metadata"]["confidence"] == 0:
                # Generate a mock confidence based on response length and processing time
                # This is just a placeholder - replace with your own logic
                mock_confidence = min(0.95, 0.5 + (len(result["response"]) / 5000) + (1 / (1 + actual_processing_time)))
                result["metadata"]["confidence"] = mock_confidence
                
            return result
        else:
            return {
                "response": f"[Error {response.status_code}] {response.text}", 
                "metadata": {
                    "processing_time": actual_processing_time,
                    "confidence": 0.0,
                    "memory_hit": False,
                    "error": True
                }
            }
    except Exception as e:
        actual_processing_time = time.time() - start_time
        return {
            "response": f"[Exception] {e}", 
            "metadata": {
                "processing_time": actual_processing_time,
                "confidence": 0.0,
                "memory_hit": False,
                "error": True
            }
        }

def display_metadata(metadata):
    """Display formatted metadata in the expander."""
    # Basic metrics with improved formatting
    st.write(f"**Processing Time:** {format_metadata_value(metadata.get('processing_time', 0))}s")
    
    confidence = metadata.get('confidence', 0)
    confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
    st.markdown(f"**Confidence:** <span style='color:{confidence_color}'>{format_metadata_value(confidence)}</span>", unsafe_allow_html=True)
    
    memory_hit = metadata.get('memory_hit', False)
    memory_color = "green" if memory_hit else "gray"
    st.markdown(f"**Memory Hit:** <span style='color:{memory_color}'>{format_metadata_value(memory_hit)}</span>", unsafe_allow_html=True)
    
    # Display agent counts if available
    agent_counts = metadata.get('agent_counts', {})
    if agent_counts:
        st.write("**Agents Used:**")
        for agent, count in agent_counts.items():
            if count > 0:
                st.write(f"- {agent}: {count}")
    
    # Display any additional metadata
    additional_metadata = {k: v for k, v in metadata.items() 
                           if k not in ['processing_time', 'confidence', 'memory_hit', 'agent_counts']}
    
    if additional_metadata:
        st.write("**Additional Details:**")
        for key, value in additional_metadata.items():
            # Format key for display
            display_key = key.replace('_', ' ').title()
            
            # Handle nested dictionaries or lists
            if isinstance(value, (dict, list)):
                st.write(f"- {display_key}:")
                st.json(value)
            else:
                st.write(f"- {display_key}: {format_metadata_value(value)}")

# Handle example question selection
if "example_clicked" in st.session_state and st.session_state.example_clicked:
    prompt = st.session_state.example_question
    st.session_state.example_clicked = False
    
    # Add to messages and process
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process the query
    response_data = chat(prompt)
    response_text = response_data.get("response", "[No response]")
    metadata = response_data.get("metadata", {})
    
    # Add the response to messages
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "metadata": metadata
    })

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            
            # Display metadata if available
            if "metadata" in msg and msg["metadata"]:
                with st.expander("Response Details"):
                    display_metadata(msg["metadata"])

# Chat input
if prompt := st.chat_input("Type your question and press Enter..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process the query
    response_data = chat(prompt)
    response_text = response_data.get("response", "[No response]")
    metadata = response_data.get("metadata", {})
    
    # Add the response to messages
    st.session_state.messages.append({
        "role": "assistant", 
        "content": response_text,
        "metadata": metadata
    })
    
    # Force a rerun to update the UI with the new messages
    st.rerun()

# Callback for example question buttons
def set_example_question(question):
    st.session_state.example_clicked = True
    st.session_state.example_question = question
    
# Show example queries in the sidebar
with st.sidebar:
    st.header("Example Questions")
    example_questions = [
        "What is the freezing point of water?",
        "Who painted the Mona Lisa?",
        "What year did World War II end?",
        "Explain the concept of quantum computing",
        "What are the main differences between Python and JavaScript?",
    ]
    
    for question in example_questions:
        if st.button(question, key=f"btn_{question}", on_click=set_example_question, args=(question,)):
            pass  # The on_click function handles the action

# Show some tips at the bottom
st.markdown("""
---
**Tips:**
1. Ask questions about general knowledge or specific topics
2. Try questions about historical events, science concepts, or technical topics
3. Use the example questions in the sidebar to see how the system responds
""")