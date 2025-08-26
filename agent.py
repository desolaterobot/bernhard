# server.py
from fastmcp import FastMCP
import os
from vector import *

mcp = FastMCP("Bernhard")

@mcp.tool
def get_document_names():
    """
    Get the names of all documents in the document folder.
    """
    names = []
    for file in os.listdir(DOCUMENT_FOLDER):
        names.append(file)
    return names

@mcp.tool
def get_full_document(document_name):
    """
    Get the full text of a document by its name.
    """
    with open(f"{DOCUMENT_FOLDER}/{document_name}", 'r') as f:
        return f.read()
    
@mcp.tool
def query_content(query):
    """
    Query the content of a document by its name.
    """
    return query_content(query)

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="127.0.0.1",
        port=4200,
        path="/info",
        log_level="debug",
    )