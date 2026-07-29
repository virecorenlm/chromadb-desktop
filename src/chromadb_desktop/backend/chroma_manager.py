import chromadb
from sentence_transformers import SentenceTransformer
import os
import logging
from typing import List, Dict, Any

class ChromaManager:
    def __init__(self, persist_directory: str = "./data/collections"):
        """Initialize ChromaDB client and embedding model"""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Load embedding model (using a small, efficient model for desktop use)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.current_collection = None
        self.logger = self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def create_collection(self, collection_name: str):
        """Create a new collection for documents"""
        try:
            self.current_collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"Collection '{collection_name}' created/loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")
            return False
    
    def get_embedding(self, text: str):
        """Generate embeddings for text"""
        return self.embedding_model.encode(text).tolist()
    
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None, ids: List[str] = None):
        """Add documents to the current collection"""
        if not self.current_collection:
            self.logger.error("No collection selected")
            return False
        
        try:
            # Generate embeddings
            embeddings = [self.get_embedding(doc) for doc in documents]
            
            # If no IDs provided, generate them
            if not ids:
                ids = [f"doc_{i}_{hash(doc) % 10000}" for i, doc in enumerate(documents)]
            
            self.current_collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas if metadatas else [{}] * len(documents),
                ids=ids
            )
            
            self.logger.info(f"Added {len(documents)} documents to collection")
            return True
        except Exception as e:
            self.logger.error(f"Error adding documents: {e}")
            return False
    
    def search(self, query: str, n_results: int = 5):
        """Search for similar documents"""
        if not self.current_collection:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.get_embedding(query)
            
            results = self.current_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            return results
        except Exception as e:
            self.logger.error(f"Error searching: {e}")
            return []
    
    def list_collections(self):
        """List all available collections"""
        return self.client.list_collections()
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            self.logger.info(f"Collection '{collection_name}' deleted")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting collection: {e}")
            return False
