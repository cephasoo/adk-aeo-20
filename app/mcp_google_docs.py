import sys
import os

# Add the project root folder to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from app.tools.google_docs_native import (
    read_google_doc,
    create_google_doc,
    append_to_google_doc,
    update_google_doc
)

# Create an MCP server
mcp = FastMCP("Google Docs Native")

@mcp.tool()
def read_doc(document_id_or_title: str) -> str:
    """
    Reads the textual body content of a Google Document.
    
    Args:
        document_id_or_title: The unique document ID or Document Title.
    """
    return read_google_doc(document_id_or_title)

@mcp.tool()
def create_doc(title: str) -> str:
    """
    Creates a new Google Document and returns its URL.
    
    Args:
        title: The title of the new document.
    """
    return create_google_doc(title)

@mcp.tool()
def append_doc(document_id_or_title: str, text: str) -> str:
    """
    Appends a text block to the end of a Google Document.
    
    Args:
        document_id_or_title: The target document ID or Document Title.
        text: The text string to append.
    """
    return append_to_google_doc(document_id_or_title, text)

@mcp.tool()
def update_doc(document_id_or_title: str, new_content: str) -> str:
    """
    Replaces the entire body content of a Google Document with new text (atomic delete-then-insert).
    
    Args:
        document_id_or_title: The target document ID or Document Title.
        new_content: The new text content to replace the document body.
    """
    return update_google_doc(document_id_or_title, new_content)

if __name__ == "__main__":
    mcp.run()
