import os
from typing import List, Dict, Union

from vector import *  # provides DOCUMENT_FOLDER, query_content, extract_pdf
import spire.doc
import markdown_pdf

from strands import tool

@tool
def get_document_names():
    """
    Get the names of all stored documents.
    """
    names = []
    for file in os.listdir(DOCUMENT_FOLDER):
        names.append(file)
    return names

@tool
def get_full_document(document_name: str):
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

@tool
def get_document_page(document_name: str, page_number: int):
    """
    Get a specific page of a document by its name. Call get_document_names() to input the exact name.
    Args:
        str: The document name from get_document_names() list.
        int: The page number to retrieve (1-indexed).
    Returns:
        str|list: The full text of the document if the document is a txt. If it is a pdf, a list of strings, each representing a page.
    """
    if document_name.endswith('.txt'):
        with open(f"{DOCUMENT_FOLDER}/{document_name}", 'r') as f:
            return f.read()
    elif document_name.endswith('.pdf'):
        return extract_pdf(f"{DOCUMENT_FOLDER}/{document_name}")[page_number-1]

@tool
def semantic_search(query):
    """
    Semantically search for relevant sections of the stored documents based on the query.
    Args:
        str: A search query.
    Returns:
        list: Containing sections and metadata regarding its Source, Page, Chunk, and Distance.
    """
    return query_content(query)

@tool
def create_document(document_name, markdown_string):
    """
    Create a new document. Documents created must be strictly written in markdown, and are stored as .md files.
    Can also be used to modify documents by using the exact same document name. Contents will be overwritten.
    Args:
        str: The name of the document to create, with .md extension.
        str: The markdown contents of the document.
    Returns:
        str: The absolute path to the created document.
    """
    if not document_name.endswith('.md'):
        document_name += '.md'
    filename = f"created_documents/{document_name}"
    with open(filename, 'w') as f:
        f.write(markdown_string)
    return os.path.abspath(filename)

@tool
def get_created_documents():
    """
    Get a list of names of all created markdown documents.
    """
    return [f for f in os.listdir("created_documents") if f.endswith('.md')]

@tool
def read_created_document(document_name: str):
    """
    Get the content of a created markdown document.
    Args:
        str: The name of the document to read.
    Returns:
        str|list: The content of the document.
    """
    if not os.path.exists(f"created_documents/{document_name}"):
        return f"No documents named {document_name}. Use get_created_documents() to find the exact name."
    if document_name.endswith('.md'):
        with open(f"created_documents/{document_name}", 'r') as f:
            return f.read()
    else:
        return f"Only created markdown documents are supported, found {document_name}."

@tool
def convert_markdown_document(document_name, document_type):
    """
    Convert a markdown document to another format. Only use this if the client says so.
    Args:
        str: The name of the document to read.
        str: The type of the document to convert to (pdf or docx).
    Returns:
        str: The absolute path to the converted document.
    """
    if not os.path.exists(f"created_documents/{document_name}"):
        return f"No documents named {document_name}. Use get_created_documents() to find the exact name."
    if document_type == "pdf":
        pdf = markdown_pdf.MarkdownPdf()
        with open(f"created_documents/{document_name}", 'r') as f:
            pdf.add_section(markdown_pdf.Section(f.read()))
        pdf.save(f"created_documents/{document_name}.pdf")
    elif document_type == "docx":
        document = spire.doc.Document()
        document.LoadFromFile(f"created_documents/{document_name}", spire.doc.FileFormat.Markdown)
        document.SaveToFile(f"created_documents/{document_name}.docx", spire.doc.FileFormat.Docx2016)
    else:
        return "Unknown type of document, only supports pdf or docx."
    return os.path.abspath(f"created_documents/{document_name}.{document_type}")
