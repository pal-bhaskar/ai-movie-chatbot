"""
MCP tool server exposing database query and semantic search tools for the AI Movie Chatbot.

This module defines MCP tools to:
- run read-only SQL queries against the local MySQL movies database
- run Cypher queries against the local Neo4j movie/person graph
- perform semantic similarity search against ChromaDB plot embeddings

It starts a FastMCP server (SSE transport) on localhost:8080 when executed as a script.
"""
from mcp.server.fastmcp import FastMCP
import mysql.connector
from neo4j import GraphDatabase
import chromadb
from chromadb.utils import embedding_functions
import os

# Initialize the FastMCP server
mcp = FastMCP("MovieDataServer")

# --- Eagerly load the model at startup ---
print("Loading ChromaDB embedding model into memory... (This may take a moment)")
emb_fn = embedding_functions.DefaultEmbeddingFunction()
print("Model loaded successfully!")
# ---------------------------------------------------

@mcp.tool()
def query_sql(sql_query: str) -> str:
    """Execute a read-only SQL query on the MySQL movies database.

    Returns a formatted string of query results or an error message.
    """
    try:
        conn = mysql.connector.connect(host="127.0.0.1", user="root", password="rootpassword", database="movies_db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        # Format output
        if not rows:
            return "No results found."
        columns = [col[0] for col in cursor.description]
        result_str = " | ".join(columns) + "\n"
        for row in rows:
            result_str += " | ".join(str(val) for val in row) + "\n"

        conn.close()
        return result_str
    except Exception as e:
        return f"SQL Error: {str(e)}"

@mcp.tool()
def query_cypher(cypher_query: str) -> str:
    """Execute a Cypher query on the Neo4j movie/person graph.

    Returns serialized record data or an error message.
    """
    try:
        driver = GraphDatabase.driver("bolt://127.0.0.1:7687", auth=("neo4j", "password"))
        with driver.session() as session:
            result = session.run(cypher_query)
            records = [str(record.data()) for record in result]
        driver.close()
        return "\n".join(records) if records else "No results found."
    except Exception as e:
        return f"Cypher Error: {str(e)}"

@mcp.tool()
def semantic_search(prompt: str) -> str:
    """Perform a semantic similarity search in ChromaDB using plot summaries.

    Returns a list of matching movies (title + id) or an error message.
    """
    try:
        client = chromadb.HttpClient(host="127.0.0.1", port=8000)
        # Pass the pre-loaded embedding function here
        collection = client.get_collection("movie_plots", embedding_function=emb_fn)
        results = collection.query(query_texts=[prompt], n_results=3)
        
        output =[]
        for i in range(len(results['ids'][0])):
            meta = results['metadatas'][0][i]
            output.append(f"Movie: {meta['title']} (ID: {meta['movieId']})")
        return "\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Vector DB Error: {str(e)}"

if __name__ == "__main__":
    # The official MCP SDK looks for the PORT environment variable
    os.environ["PORT"] = "8080"
    # Serve tools over Server-Sent Events locally on port 8080
    print("Starting MCP Tool Server on http://localhost:8080")
    mcp.run(transport="sse")