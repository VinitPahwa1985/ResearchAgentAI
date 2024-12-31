import streamlit as st
from phi.agent import Agent, RunResponse
from phi.model.openai import OpenAIChat
from phi.tools.duckduckgo import DuckDuckGo
from phi.tools.newspaper4k import Newspaper4k
from phi.utils.pprint import pprint_run_response

import os
from dotenv import load_dotenv
from typing import Iterator
import logging
import contextlib
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Access the variables
openai_api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"OpenAI API Key: {openai_api_key}")

# Create agent
agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGo(), Newspaper4k()],
    description="You are a senior The Wall Street Journal researcher writing an article on a topic.",
    instructions=[
        "For a given topic, search for the top 5 links.",
        "Then read each URL and extract the article text, if a URL isn't available, ignore it.",
        "Analyse and prepare an NYT worthy article based on the information.",
    ],
    markdown=True,
    show_tool_calls=True,
    add_datetime_to_instructions=True,
)
# Function to capture pprint_run_response output
def capture_pprint_run_response(response_stream: Iterator[RunResponse]) -> str:
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        pprint_run_response(response_stream, markdown=True, show_time=True)
        return buf.getvalue()

# Function to clean and format the output
def clean_output(output: str) -> str:
    # Remove special characters and unnecessary formatting
    cleaned_output = output.replace('╭', '').replace('╮', '').replace('│', '').replace('╯', '').replace('╰', '')
    cleaned_output = cleaned_output.replace('┏', '').replace('┓', '').replace('┗', '').replace('┛', '')
    cleaned_output = cleaned_output.replace('━', '').replace('┃', '')
    
    # Remove lines containing 'WARNING' and 'Response Running'
    lines = cleaned_output.split('\n')
    relevant_lines = []
    for line in lines:
        if 'WARNING' not in line and 'Response Running' not in line:
            relevant_lines.append(line.strip())
    
    return '\n'.join(relevant_lines).strip()


# Function to run the agent and display the response
def run_agent(topic: str):
    try:
        logger.info(f"Running agent for topic: {topic}")
        response_stream: Iterator[RunResponse] = agent.run(topic, stream=True)
        
        # Capture and clean the response
        response_output = capture_pprint_run_response(response_stream)
        cleaned_output = clean_output(response_output)
        
        # Display the cleaned response
        st.markdown("### Response Stream")
        st.markdown(cleaned_output.replace('\n', '  \n'))  # Ensure newlines are rendered correctly
        
        logger.info("Agent run completed successfully")
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        st.error(f"An error occurred: {e}")

# Streamlit app layout
st.title("The Wall Street Journal Researcher Agent")
topic = st.text_input("Enter a topic to research:", "Oracle Group")

if st.button("Run Agent"):
    run_agent(topic)