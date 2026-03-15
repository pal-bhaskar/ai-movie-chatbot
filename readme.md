Here is a comprehensive, step-by-step guide to building your Full-Stack Local AI Movie Chatbot.

**We will use Docker Compose for the databases, FastMCP (part of the official Model Context Protocol SDK) for the tool servers, Ollama for local inference, and Streamlit / LangChain for the conversational UI.**

## Step 1: Project Setup & Prerequisites

First, ensure you have Docker andOllama installed locally.
Pull a capable tool-calling model in your terminal (we'll use llama3.2 or llama3.1):

```console
ollama run llama3.1
```
Create a new project folder and save your 3 CSV files (**movies_metadata.csv, ratings.csv, plots.csv**) inside it.

Open your terminal and install the langgraph package:
```console
pip install langgraph
```

Create a requirements.txt file and install the dependencies.

Run: 
```console
pip install -r requirements.txt
```
## Step 2: Infrastructure (docker-compose.yml)

Create a docker-compose.yml file to run MySQL, Neo4j, and ChromaDB locally.

Start your databases by running: 
```console
docker compose up -d
```
## Step 3: Data Ingestion

This script loads the CSV data into all three databases. Run **ingest_data.py** once after the Docker containers are healthy.

Run: 
```python
python ingest_data.py
```

## Step 4: MCP Servers 

Using the official mcp SDK, we define a unified FastMCP application that binds all three Local AI tools into a single server instance. We will host this using Server-Sent Events (SSE) so Streamlit can easily communicate with it. Add **mcp_servers.py**.

Run in a separate terminal and leave running: 
```python
python mcp_servers.py
```
## Step 5: Streamlit Orchestrator UI

The file **app.py** contains the UI and orchestrates LangChain to intelligently route requests to your running MCP Tool Server.

## Final Running Instructions

* Start databases: docker compose up -d
* Run data ingest: python ingest_data.py (Let it finish)
* In Terminal 1, start the MCP Tool Server: python mcp_servers.py
* In Terminal 2, start the Streamlit frontend: streamlit run app.py