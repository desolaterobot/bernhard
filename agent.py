# server.py
from fastmcp import FastMCP
import os
from vector import *

mcp = FastMCP("Bernhard")

@mcp.tool
def get_document_names():
    """
    Get the names of all stored documents.
    """
    names = []
    for file in os.listdir(DOCUMENT_FOLDER):
        names.append(file)
    return names

@mcp.tool
def get_full_document(document_name:str):
    """
    Get the full text of a document by its name. Call get_document_names() to input the exact name.
    Args:
        str: The document name from get_document_names() list.
    Returns:
        str|list: The full text of the document if the document is a txt. If it is a pdf, a list of strings, each representing a page.
    """
    if document_name.endswith('.txt'):
        with open(f"{DOCUMENT_FOLDER}/{document_name}", 'r') as f:
            return f.read()
    elif document_name.endswith('.pdf'):
        return extract_pdf(f"{DOCUMENT_FOLDER}/{document_name}")

@mcp.tool
def semantic_search(query):
    """
    Semantically search for relevant sections of the stored documents based on the query.
    Args:
        str: A search query.
    Returns:
        list: Containing sections and metadata regarding its Source, Page, Chunk, and Distance.
    """
    return query_content(query)

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=4200,
        path="/papers",
        log_level="debug",
    )