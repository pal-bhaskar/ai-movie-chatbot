"""
Streamlit web app for the AI Movie Chatbot.

This module implements the Streamlit UI and ties together the backend services:
- MySQL / Neo4j / ChromaDB ingestion (via `ingest_data.py`)
- MCP tool server (via `mcp_servers.py`)
- LangChain agent logic for answering questions and executing tool calls

Typical usage
-------------
Run the app locally with:

    streamlit run src/app.py

Requirements
------------
- Streamlit installed in the active Python environment
- Local services running as expected:
    * MySQL on localhost (movies_db)
    * Neo4j on bolt://localhost:7687
    * ChromaDB on localhost:8000
- `resources/` data files present for ingestion

This file contains:
- UI layout and interaction handlers
- Initialization of the LangChain agent and tool wrappers
- Optional ingestion / startup logic (if present)
"""
import streamlit as st
import asyncio
from datetime import timedelta
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession
from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
import logging
import logging_loki

# --- Setup Loki Logging for UI ---
handler = logging_loki.LokiHandler(
    url="http://127.0.0.1:3100/loki/api/v1/push",
    tags={"app": "movie-bot", "component": "streamlit-ui"},
    version="1",
)
logger = logging.getLogger("streamlit-ui")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

logger.info("Starting MCP Server initialization...")
# ---------------------------------


# --- 1. Async MCP Tool Wrapper ---
async def call_mcp_tool(tool_name: str, args: dict) -> str:
    """Connects to the running FastMCP SSE server and executes a tool."""
    async with sse_client("http://127.0.0.1:8080/sse") as streams:
        # Increase read timeout to 60 seconds
        async with ClientSession(streams[0], streams[1], read_timeout_seconds=timedelta(seconds=60)) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return result.content[0].text

# Synchronous wrappers for LangChain Tools
def run_sql(query: str):
    try:
        return asyncio.run(call_mcp_tool("query_sql", {"sql_query": query}))
    except Exception as e:
        return f"Tool Error: Failed to execute SQL query. Details: {str(e)}"

def run_cypher(query: str):
    try:
        return asyncio.run(call_mcp_tool("query_cypher", {"cypher_query": query}))
    except Exception as e:
        return f"Tool Error: Failed to execute Graph query. Details: {str(e)}"

def run_vector(query: str):
    try:
        return asyncio.run(call_mcp_tool("semantic_search", {"prompt": query}))
    except Exception as e:
        return f"Tool Error: Failed to execute Vector search. Details: {str(e)}"

# --- 2. Langchain Tools Definition ---
tools =[
    Tool(
        name="query_sql",
        func=run_sql,
        description="Fetch budget, release_year, ratings, num_votes. SQL Schema: movies(id INT, title VARCHAR, budget FLOAT, release_year INT), ratings(movie_id INT, rating FLOAT, num_votes INT). ALWAYS append 'LIMIT 20' to your queries so you don't crash the system with too much data."
    ),
    Tool(
        name="query_cypher",
        func=run_cypher,
        description="Find actors, directors, cast relationships. Graph Schema: (:Movie {movieId, title}), (:Person {name}), (:Person)-[:ACTED_IN]->(:Movie), (:Person)-[:DIRECTED]->(:Movie)."
    ),
    Tool(
        name="semantic_search",
        func=run_vector,
        description="Use this tool when the user asks about movie PLOTS, genres, themes, or feelings (e.g., 'A movie about space travel'). Pass the description as a plain string."
    )
]

# --- 3. Initialize Agent State ---
st.set_page_config(page_title="Local AI Movie Chatbot", layout="wide")

# LangGraph natively uses a list of messages for memory
if "messages" not in st.session_state:
    st.session_state.messages =[]

if "agent" not in st.session_state:
    llm = ChatOllama(model="llama3.1", temperature=0, base_url="http://127.0.0.1:11434")
    
    # create_react_agent is the modern LangGraph replacement for AgentExecutor
    st.session_state.agent = create_react_agent(llm, tools=tools)

# --- 4. Streamlit UI ---
st.title("🍿 Local AI Movie Chatbot")
st.markdown("*Powered by Ollama, Docker, LangGraph, and MCP*")

# Display Chat History (Filtering out the hidden tool-call data)
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant"):
            st.write(msg.content)

# Chat Input
if prompt := st.chat_input("Ask a question about movies..."):
    logger.info(f"User prompt received: {prompt}")
    with st.chat_message("user"):
        st.write(prompt)
    
    # 1. Add user message to memory
    st.session_state.messages.append(HumanMessage(content=prompt))

    with st.chat_message("assistant"):
        with st.spinner("Analyzing and querying databases via MCP tools..."):
            try:
                # 2. Invoke the LangGraph agent with the entire conversation history
                result = st.session_state.agent.invoke({"messages": st.session_state.messages})
                
                # 3. The result contains the updated message history (including tool logic)
                updated_messages = result["messages"]
                
                # 4. Display the final AI response
                final_ai_msg = updated_messages[-1]

                # Log the AI's final answer
                logger.info(f"AI Response: {final_ai_msg.content}")

                st.write(final_ai_msg.content)
                
                # 5. Save the new state back to memory so the bot remembers the conversation
                st.session_state.messages = updated_messages
                
            except Exception as e:
                logger.error(f"UI Orchestration Error: {str(e)}")
                st.error(f"Error: {str(e)}")