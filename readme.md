Here is a comprehensive, step-by-step guide to building your Full-Stack Local AI Movie Chatbot.

**We will use Docker Compose for the databases, FastMCP (part of the official Model Context Protocol SDK) for the tool servers, Ollama for local inference, and Streamlit / LangChain for the conversational UI.**

## Step 1: Project Setup & Prerequisites

First, ensure you have Docker andOllama installed locally.
Pull a capable tool-calling model in your terminal (we'll use llama3.2 or llama3.1):

```console
ollama run llama3.1
```
Create a new project folder and save your 3 CSV files (**movies_metadata.csv, ratings.csv, plots.csv**) inside it.

Open your terminal and install the langgraph, logging framework packages:
```console
pip install langgraph
pip install python-logging-loki
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
```python 
streamlit run app.py 
```

## Final Running Instructions

* Start databases: docker compose up -d
* Run data ingest: ```python ingest_data.py``` (Let it finish)
* In Terminal 1, start the MCP Tool Server: ```python mcp_servers.py ```
* In Terminal 2, start the Streamlit frontend: ```streamlit run app.py ```
* To stop docker containers: ```docker-compose -f docker-compose.yml down -v -t 0```

## Access/ Query MySQL DB
If you prefer a visual interface to see your tables, run queries, and explore the data, you can download a free SQL client like DBeaver, MySQL Workbench, or TablePlus.

Because your docker-compose.yml mapped port 3306 to your laptop, you can connect to it exactly as if MySQL was installed directly on your machine.

Use these connection details in your GUI tool:
* Host: 127.0.0.1 (or localhost)
* Port: 3306
* Username: root
* Password: rootpassword
* Database: movies_db

## View Your Logs in Grafana

Now that your Python app is generating and pushing logs, let's look at them in Grafana!

Open Grafana: Go to http://localhost:3000 in your web browser.

Log In: Enter the username admin and password admin.

### Connect Loki:
* In the left sidebar, go to **Connections > Data sources**.
* Click **Add data source** and select **Loki**.
* Under the **URL** field, type exactly: http://loki:3100 *(Note: Use **loki**, not localhost, because Grafana connects to Loki inside the internal Docker network).*
* Scroll down and click **Save & Test**. You should see a green "Data source connected and labels found" message.

### View Your Logs:
* In the left sidebar, click on the compass icon labeled Explore.
* In the dropdown at the top left, ensure **Loki** is selected.
* Under the Label filters section, select **app = movie-bot**.
* Click the big blue **Run query** button in the top right.

## Peek into Neo4j

The official Neo4j Browser allows you to visually explore the nodes (Movies, Persons) and relationships (ACTED_IN, DIRECTED) that you created during your ingestion script.

Here is how to visualize your graph and its ontology:
### 1. Open Neo4j Browser

* Open your web browser and navigate to http://localhost:7474.
* You will be greeted by a login screen. Connect using the credentials you defined in your **docker-compose.yml**:
   *  Connect URL: neo4j://localhost:7687
   * Database: neo4j
   * Username: neo4j
   * Password: password
* Click **Connect**.

### 2. Visualize the Ontology (Database Schema)

To see a high-level overview of how your data is structured (your ontology), run this command in the query bar at the top of the screen:

```console
CALL db.schema.visualization()
```

Press the blue **Play** button on the right of the query bar to run it.

#### What you will see:
A visual diagram showing a Movie node, a Person node, and arrows indicating the ACTED_IN and DIRECTED relationships connecting them. This confirms your graph schema was created correctly.

### 3. Visualize the Actual Graph Data

To see the actual movies, actors, and directors connected together, you can run queries that return paths.

Try running this query in the bar at the top to see a random sample of 25 movies and the people connected to them:

```console
MATCH p=(:Person)-
```