import logging
from app.graph.state import TruthLensState
from app.services.rag import RAGService

logger = logging.getLogger(__name__)

def retrieval_node(state: TruthLensState) -> dict:
    logger.info("Retrieval node processing phase started.")
    try:
        rag = RAGService()

        claims = state.get("claims", [])
        if not claims:
            logger.warning("No claims found in state context. Bypassing retrieval node.")
            return {
                "evidence_data": {},
                "evidence_sources": {}
            }

        evidence_data, evidence_sources = rag.retrieve_evidence_for_claim(claims)
        
        logger.info(f"Successfully retrieved evidence for {len(claims)} claims.")

        for claim_obj in claims:
            claim_text = claim_obj.get("claim", "")
            search_query = claim_obj.get("search_query", claim_text)
            
            if evidence_sources.get(claim_text) == "web_fallback":
                new_evidence = evidence_data.get(claim_text, [])
                if new_evidence:
                    logger.info(f"Triggering cache upsert for newly found web evidence on claim: '{claim_text[:30]}...'")
                    rag.cache_new_findings(
                        claim=claim_text, 
                        search_query=search_query, 
                        evidence=new_evidence
                    )

        # CRITICAL FIX: Return ONLY the updated retrieval keys
        return {
            "evidence_data": evidence_data,
            "evidence_sources": evidence_sources
        }

    except Exception as node_error:
        error_msg = f"Fatal system interruption in retrieval node: {str(node_error)}"
        logger.error(error_msg)
        return {"error": error_msg}