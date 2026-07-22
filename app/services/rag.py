"""
RAG Service Module

Orchestrates the hybrid knowledge retrieval pipeline for TruthLens:
1. Generates vectors for contextually resolved claims via Google GenAI.
2. Queries the local ChromaDB vector store for semantic batch matches.
3. Evaluates similarity distance margins to determine whether to utilize local cache contents.
4. Distributes query requests to Tavily Web Search fallback when local data is missing or weak.
"""

import logging
import hashlib
from typing import List, Dict, Any, Tuple 

# Core database utilities and wrapper services
from app.db.embeddings import EmbeddingEngine 
from app.db.vector_store import VectorStoreClient 
from app.services.search import SearchService

# Initialize logger using standard module-level resolution
logger = logging.getLogger(__name__)


class RAGService: 
    """
    High-level orchestrator implementing local semantic cache evaluation 
    before falling back to live web search distribution.
    """

    def __init__(self, similarity_threshold: float = 0.85): 
        """
        Initializes the hybrid RAG orchestration service wrapper.

        Args:
            similarity_threshold (float, optional): Score minimum (0.0 to 1.0) required 
                                                 to use cached DB context instead of 
                                                 performing a live search. Defaults to 0.85.
        """
        self.embedding_engine = EmbeddingEngine() 
        self.vector_store = VectorStoreClient() 
        self.search_fallback = SearchService() 
        self.threshold = similarity_threshold 
        logger.info(f"RAG Service is online. Authorized threshold set to: {self.threshold}")

    def retrieve_evidence_for_claim(self, claims: List[Dict[str, str]]) -> Tuple[Dict[str, Any], Dict[str, str]]: 
        """
        Iterates over a collection of extracted claims, selecting optimal data 
        sourcing via vector proximity analytics.

        Args:
            claims (List[Dict[str, str]]): List of claim dictionaries from ClaimService 
                                           containing 'claim' and 'search_query'.

        Returns:
            Tuple[Dict[str, Any], Dict[str, str]]:
                - Combined evidence results mapped by original claim string.
                - Sourcing matrix tracking 'database' vs 'web_fallback' designations per claim.
        """
        evidence_results = {} 
        evidence_sources = {} 

        for claim_obj in claims: 
            claim_text = claim_obj.get("claim", "")
            search_query = claim_obj.get("search_query", claim_text)

            if not claim_text: 
                continue 

            logger.info(f"Evaluating the sourcing data channel for the claim: '{claim_text}'")

            try: 
                # 1. Compute query vector embedding coordinates via Google GenAI (768 dimensions)
                query_vector = self.embedding_engine.get_embedding(search_query)

                # 2. Retrieve top matching records from ChromaDB collection
                db_matches = self.vector_store.search_similarity(query_vector)

                # 3. Analyze confidence metrics (the list is pre-sorted by closest match distance first)
                if db_matches and db_matches[0]["score"] >= self.threshold: 
                    logger.info(f"🎯 RAG Hit! Reusing the cached evidence. Top match score: {db_matches[0]['score']:.2f}")

                    combined_cached_evidence = [] 
                    for match in db_matches: 
                        # Aggregate sub-sources for all records passing the threshold boundary
                        if match["score"] >= self.threshold: 
                            combined_cached_evidence.extend(match["evidence"])

                    evidence_results[claim_text] = combined_cached_evidence
                    evidence_sources[claim_text] = "database"

                else: 
                    # Evaluate and log the failure condition context
                    if db_matches: 
                        logger.info(f"⚠️ Top match score ({db_matches[0]['score']:.2f}) is below confidence threshold.")
                    else: 
                        logger.info("⚠️ No matching historical records found in local vector storage.")

                    logger.info("Sourcing context live from Tavily Web Search fallback.")

                    # 4. Trigger fallback web crawl query using the optimized keyword search string
                    web_results = self.search_fallback.search_evidence([search_query])
                    extracted_evidence = web_results.get(search_query, [])

                    evidence_results[claim_text] = extracted_evidence
                    evidence_sources[claim_text] = "web_fallback"

            except Exception as e: 
                logger.error(f"Error processing the RAG Pipeline for claim '{claim_text}': {str(e)}")
                # Soft recovery fallback choice to prevent pipeline graph execution failures
                evidence_results[claim_text] = []
                evidence_sources[claim_text] = "error_fallback"

        return evidence_results, evidence_sources 

    def cache_new_findings(self, claim: str, search_query: str, evidence: List[Dict[str, str]]) -> bool: 
        """
        Caches a newly discovered web evidence payload into ChromaDB for future processing hits.

        Args:
            claim (str): The contextually resolved raw text statement of the claim.
            search_query (str): The keyword-optimized string used to query search engines.
            evidence (List[Dict[str, str]]): List of dict blocks containing title, url, snippet fields.

        Returns:
            bool: True if write tracking operations completed without fault, False otherwise.
        """
        try: 
            if not evidence: 
                logger.warning(f"Skipping cache write task for claim '{claim}': No evidence payload provided.")
                return False

            # Generate a deterministic SHA-256 identifier string to guarantee deduplication rules
            claim_id = hashlib.sha256(claim.encode('utf-8')).hexdigest()[:16]

            # Generate embedding using the target query for maximum cache retrieval accuracy
            vector = self.embedding_engine.get_embedding(search_query)

            # Commit record payload straight to the local persistent database volume client
            self.vector_store.upsert_vector(
                vector=vector, 
                claim_id=claim_id, 
                document_text=claim, 
                evidence_payload=evidence 
            )

            logger.info(f"Successfully cached verified context into Vector DB under reference ID: {claim_id}")
            return True 

        except Exception as cache_error: 
            logger.error(f"Failed to update the cache repository client storage: {str(cache_error)}")
            return False


# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__": 
    import sys 
    
    # Configure root standalone logger metrics matching TruthLens layout rules
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    print("\n--- Testing RAG Orchestration Layer ---")

    mock_claim_input = [
        {
            "claim": "Google Gemini Embedding API outputs text-embeddings across variable dimensions.",
            "search_query": "Google Gemini embedding models dimension sizing limits"
        }
    ]
    
    # Initialize orchestration class with relaxed target boundaries for testing validation
    rag = RAGService(similarity_threshold=0.80)

    # Run verification execution cycle
    evidence_data, mapping_source = rag.retrieve_evidence_for_claim(mock_claim_input)
    
    print("\n--- Pipeline Sourcing Validation Results ---")
    import json
    print("Evidence Data Payload Preview:")
    print(json.dumps(evidence_data, indent=4))
    print("\nSource Mapping Matrix Trace:")
    print(json.dumps(mapping_source, indent=4))
    print("\n✅ Service layer operational verification step complete.\n")