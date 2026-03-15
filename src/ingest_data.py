import pandas as pd
import mysql.connector
from neo4j import GraphDatabase
import chromadb
from chromadb.utils import embedding_functions
import time

def ingest_mysql():
    print("Ingesting MySQL...")
    conn = mysql.connector.connect(host="localhost", user="root", password="rootpassword", database="movies_db")
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INT PRIMARY KEY, title VARCHAR(255), budget FLOAT, release_year INT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            movie_id INT PRIMARY KEY, rating FLOAT, num_votes INT,
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
    """)
    
    # Load metadata
    df_movies = pd.read_csv('resources/movies_metadata.csv').fillna(0)
    for _, row in df_movies.iterrows():
        cursor.execute(
            "INSERT IGNORE INTO movies (id, title, budget, release_year) VALUES (%s, %s, %s, %s)",
            (int(row['id']), str(row['title']), float(row['budget']), int(row['release_year']))
        )
        
    # Load ratings
    df_ratings = pd.read_csv('resources/ratings.csv').fillna(0)
    for _, row in df_ratings.iterrows():
        cursor.execute(
            "INSERT IGNORE INTO ratings (movie_id, rating, num_votes) VALUES (%s, %s, %s)",
            (int(row['movie_id']), float(row['rating']), int(row['num_votes']))
        )
        
    conn.commit()
    conn.close()
    print("MySQL Ingestion Complete.")

def ingest_neo4j():
    print("Ingesting Neo4j...")
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    df_movies = pd.read_csv('resources/movies_metadata.csv').fillna("")
    
    with driver.session() as session:
        # Constraints
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie) REQUIRE m.movieId IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE")
        
        for _, row in df_movies.iterrows():
            m_id = int(row['id'])
            title = str(row['title'])
            
            # Placeholder actors and directors as requested
            actor_name = f"Star of {title}"
            director_name = f"Director of {title}"
            
            query = """
            MERGE (m:Movie {movieId: $m_id})
            SET m.title = $title
            MERGE (a:Person {name: $actor_name})
            MERGE (d:Person {name: $director_name})
            MERGE (a)-[:ACTED_IN]->(m)
            MERGE (d)-[:DIRECTED]->(m)
            """
            session.run(query, m_id=m_id, title=title, actor_name=actor_name, director_name=director_name)
    driver.close()
    print("Neo4j Ingestion Complete.")

def ingest_chromadb():
    print("Ingesting ChromaDB...")
    client = chromadb.HttpClient(host="localhost", port=8000)
    # Uses sentence-transformers internally (all-MiniLM-L6-v2) to embed locally
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    
    collection = client.get_or_create_collection(name="movie_plots", embedding_function=emb_fn)
    
    df_plots = pd.read_csv('resources/plots.csv').fillna("")
    ids, docs, metadatas = [], [],[]
    
    for idx, row in df_plots.iterrows():
        ids.append(str(row['movie_id']))
        docs.append(str(row['plot_summary']))
        metadatas.append({"movieId": int(row['movie_id']), "title": str(row['title'])})
        
    # Batch add
    if ids:
        collection.add(documents=docs, metadatas=metadatas, ids=ids)
    print("ChromaDB Ingestion Complete.")

if __name__ == "__main__":
    # Give DBs a few seconds to fully spin up
    time.sleep(5)
    ingest_mysql()
    ingest_neo4j()
    ingest_chromadb()