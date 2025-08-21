import chromadb
from hashlib import sha256
import os

client = chromadb.PersistentClient(path="vectordata") # path to data storage
collection = client.get_or_create_collection(name="contents")

def store_content(name, content):
    """
    Store the content of a paper in ChromaDB. Splits them, vectorizes them, then stores them.
    """
    chunks = content.split("\n\n") #TODO: improve text splitting function to split the paper format better? For now split based on paragraphs.
    collection.add(
        ids=[sha256(chunk.encode()).hexdigest() for chunk in chunks], # for now just use sha256 for chunk ID
        documents=[chunk for chunk in chunks],
        metadatas=[{"name": name, "chunk_number": i} for i, _ in enumerate(chunks)] # additional data for each chunk, can put document title, page, section name...
    )

def query_content(query, N=5):
    """
    Query the content of a paper in ChromaDB, returns the top N most relevant chunks from the documents.
    """
    results = collection.query(
        query_texts=[query],
        n_results=N
    )
    return results

def print_query_results(query_results):
    """
    Print the results of a query to the console.
    """
    for document, distance, metadata in zip(query_results['documents'][0], query_results['distances'][0], query_results['metadatas'][0]):
        print("="*50)
        print(f"Source: {metadata['name']}, Chunk #{metadata['chunk_number']}")
        print(f"Vector Distance: {distance}")
        print("Content:")
        print(document)
        print("="*50)

if __name__ == "__main__":
    while True:
        instructions = "Query (q), Store (s), Exit (e): "
        inp = input(instructions).lower()
        if inp == "q":
            query = input("Enter your query: ")
            print_query_results(query_content(query))
        elif inp == "s":
            for document in os.listdir("documents"):
                with open(os.path.join("documents", document), "r") as f:
                    print(f"Storing content from {document}...")
                    content = f.read()
                    store_content(document, content)
        elif inp == "e":
            break