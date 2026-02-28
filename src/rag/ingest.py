import chromadb
from chromadb.utils import embedding_functions

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)

client = chromadb.PersistentClient(path="./aibou_vector_db")

collection = client.get_or_create_collection(
    name="personal_projects",
    embedding_function=ollama_ef
)

documents = [
    "The DANGAI website is a personal project built using React, TypeScript, and Node.js.",
    "The automated trading bot is written in Go and uses login credentials to connect to the Flattrade platform.",
    "Aegis is a privacy-preserving federated learning project designed for heart disease prediction."
]

ids = ["chunk_1", "chunk_2", "chunk_3"]

print("Spinning up nomic-embed-text. Converting text to vectors and saving to ChromaDB.")

collection.add(
    documents=documents,
    ids=ids
)

print("\nSuccess! The facts have been mathematically embedded into Aibou's deep memory.")