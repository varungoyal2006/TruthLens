"""
Vector Store Client Module

Manages ChromaDB collections, local disk persistence inside the tmp/ directory, 
vector query similarity scoring, and context upsertions.
"""

import os
import logging
import sys
from typing import List, Dict, Any
import json
import chromadb

# Initialize logger using standard module-level resolution
logger = logging.getLogger(__name__)

# Resolve absolute path to the local temporary storage directory (12-Factor style)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROMA_PERSIST_DIR = os.path.join(PROJECT_ROOT, "tmp", "chroma_db")


class VectorStoreClient:
    """
    Encapsulated ChromaDB interface handling data storage, batch retrieval, 
    and similarity lookup tasks.
    """

    def __init__(self, collection_name: str = "verified_claims"):
        """
        Initializes persistent disk storage for ChromaDB.

        Args:
            collection_name (str, optional): Name of the target collection. 
                                            Defaults to "verified_claims".
        """
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        
        # Initialize the persistent client (equivalent to standard standalone server storage)
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        
        # Create or fetch the existing collection
        # Configured with Cosine Distance calculation metric space
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} 
        )
        logger.info(f"Connected to local ChromaDB collection: '{collection_name}' at {CHROMA_PERSIST_DIR}")

    def search_similarity(self, query_vector: List[float], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB using a raw embedding vector to find the top N nearest matches.

        Args:
            query_vector (List[float]): Vector array representing the claim query.
            limit (int, optional): Number of top results to return. Defaults to 3.

        Returns:
            List[Dict[str, Any]]: A list of match structures containing metadata, documents, 
                                  and normalized similarity scores, sorted by proximity.
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=limit
            )
            
            # Guard clause against empty database queries or miss states
            if not results or not results["ids"] or len(results["ids"][0]) == 0:
                return []

            # Unpack the list results from the first query index batch
            ids = results["ids"][0]
            distances = results["distances"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]

            matched_records = [] 

            # Map array slices into clean structured Python objects
            for i in range(len(ids)): 
                distance = distances[i] 
                # Convert Cosine Distance to a generic similarity score (1.0 - distance)
                similarity_score = 1.0 - distance 

                raw_metadata = metadatas[i].get("evidence", "[]")
                evidence_list = json.loads(raw_metadata)

                matched_records.append({
                    "id": ids[i], 
                    "score": similarity_score, 
                    "claim": documents[i], 
                    "evidence": evidence_list
                })

            return matched_records
            
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {str(e)}")
            return []

    def upsert_vector(
        self, 
        vector: List[float], 
        claim_id: str, 
        document_text: str, 
        evidence_payload: List[Dict[str, str]]
    ) -> None:
        """
        Inserts or updates a vectorized claim and its verified context inside ChromaDB.

        Args:
            vector (List[float]): The numerical vector coordinates.
            claim_id (str): A unique string identifier.
            document_text (str): The raw text representation of the claim.
            evidence_payload (List[Dict[str, str]]): List of gathered evidence items to save.
        """
        try:
            self.collection.upsert(
                ids=[claim_id],
                embeddings=[vector],
                documents=[document_text],
                metadatas=[{"evidence": json.dumps(evidence_payload)}]
            )
            logger.info(f"Successfully upserted record '{claim_id}' into ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to write record to ChromaDB: {str(e)}")
            raise e


# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__":
    # Configure standalone logger format matching app requirements
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    print("\n--- Initializing Vector Store Local Check ---")
    db = VectorStoreClient(collection_name="test_claims")
    
    # Corrected: Changed from 786 to 768 dimensions to match target Google GenAI configurations
    mock_vector = [0.1] * 768
    mock_id = "test_claim_001"
    mock_text = "ChromaDB local persistence deployment test statement."
    mock_evidence = [
        {"title": "Test Source", "url": "https://test.io", "snippet": "Verified reference data string matches test constraints."}
    ]
    
    try:
        # Test 1: Upsert
        print("\nTesting Database Upsert...")
        db.upsert_vector(
            vector=mock_vector,
            claim_id=mock_id,
            document_text=mock_text,
            evidence_payload=mock_evidence
        )
        
        # Test 2: Search Query
        print("\nTesting Database Similarity Retrieval...")
        search_result = db.search_similarity(query_vector=mock_vector, limit=1)
        print("\nMatch Result Output:")
        print(json.dumps(search_result, indent=4))
        print("\n✅ Local Vector DB layer successfully confirmed functional.\n")
        
    except Exception as err:
        print(f"\n❌ Local execution testing failed: {err}\n")