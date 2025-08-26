import chromadb
from hashlib import sha256
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pdf_parser import * # our PDF parser module!

'''
Responsible for reading, vectorizing file content and storing it in ChromaDB.
'''

client = chromadb.PersistentClient(path="vectordata") # path to data storage
collection = client.get_or_create_collection(name="contents")
DOCUMENT_FOLDER = "documents"

def split_text(content):
    """
    Split the content into chunks for processing
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,    # max size of each chunk (in characters, not tokens)
        chunk_overlap=200,  # overlap between chunks
        separators=["\n\n", "\n", " ", ""]  # splitting priority
    ) #TODO experiment with these values
    return splitter.split_text(content)
    


def store_content(file_name:str):
    """
    Store the content of a file in ChromaDB. Splits them, vectorizes them, then stores them.
    """
    print(f"Processing content from {file_name}...")
    if file_name.endswith(".txt"):
        with open(file_name, "r") as f:
            content = f.read()
            print(f"Splitting content...")
            chunks = split_text(content)
            print(f"Storing content...")
            collection.add(
                ids=[sha256(chunk.encode()).hexdigest() for chunk in chunks], # for now just use sha256 for chunk ID
                documents=[chunk for chunk in chunks],
                metadatas=[{"name": file_name, "chunk_number": i} for i, _ in enumerate(chunks)] # additional data for each chunk, can put document title, page, section name...
            )
    elif file_name.endswith(".pdf"):
        for page_number, page_content in enumerate(extract_pdf(file_name)):
            print(f"Splitting content from page {page_number}...")
            chunks = split_text(page_content)
            print(f"Storing content from page {page_number}...")
            collection.add(
                ids=[sha256(chunk.encode()).hexdigest() for chunk in chunks], # for now just use sha256 for chunk ID
                documents=[chunk for chunk in chunks],
                metadatas=[{"name": file_name, "chunk_number": i, "page_number": page_number} for i, _ in enumerate(chunks)] # additional data for each chunk, can put document title, page, section name...
            )
        
def query_content(query, N=5):
    """
    Query the content of a paper in ChromaDB, returns the top N most relevant chunks from the documents.
    """
    results = collection.query(
        query_texts=[query],
        n_results=N
    )
    results_list = []
    for document, distance, metadata in zip(results['documents'][0], results['distances'][0], results['metadatas'][0]):
        results_list.append(
            {
                "Source" : metadata['name'],
                "Page" : metadata.get('page_number', 'N/A'),
                "Chunk" : metadata['chunk_number'],
                "Distance" : distance,
                "Content" : document
            }
        )
    return results_list

def print_query_results(query_results):
    """
    Print the results of a query to the console.
    """
    for result in query_results:
        print("="*80)
        print(f"Source: {result['Source']}, Page: {result['Page']}, Chunk: {result['Chunk']}, Distance: {result['Distance']}")
        print("-"*80)
        print(result['Content'])
        print("="*80)

# run this file to vectorize and store the document
if __name__ == "__main__":
    while True:
        instructions = "Query (q), Store (s), Exit (e): "
        inp = input(instructions).lower()
        if inp == "q":
            query = input("Enter your query: ")
            print_query_results(query_content(query))
        elif inp == "s":
            for document_name in os.listdir(DOCUMENT_FOLDER):
                store_content(f"{DOCUMENT_FOLDER}/{document_name}")
        elif inp == "e":
            break