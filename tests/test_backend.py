#!/usr/bin/env python3

import sys
import os

from chromadb_desktop.backend.chroma_manager import ChromaManager
# Parser module: import from `chromadb_desktop.backend.file_parser`
from chromadb_desktop.backend.file_parser import FileParser

def test_backend():
    print("🧪 Testing ChromaDB Desktop Backend...")
    
    # Test file parser
    parser = FileParser()
    
    # Create a test file
    test_content = """
    Python is a programming language that lets you work quickly.
    ChromaDB is a vector database for embeddings.
    This is a test document for our application.
    """
    
    with open("test_document.txt", "w") as f:
        f.write(test_content)
    
    # Parse the file
    result = parser.parse_file("test_document.txt")
    print("📄 File parsing result:", result)
    
    # Test ChromaDB
    chroma = ChromaManager()
    chroma.create_collection("test_collection")
    
    # Add the parsed content
    if result["success"] and result["chunks"]:
        success = chroma.add_documents(
            documents=result["chunks"],
            metadatas=[{"source": "test_document.txt"}] * len(result["chunks"])
        )
        print("📝 Document addition:", "Success" if success else "Failed")
        
        # Test search
        results = chroma.search("programming language", n_results=2)
        print("🔍 Search results:", results)
    
    print("✅ Backend test completed!")

if __name__ == "__main__":
    test_backend()
