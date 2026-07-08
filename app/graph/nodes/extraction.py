import logging
from app.graph.state import TruthLensState
from app.services.claim import ClaimService

logger = logging.getLogger(__name__)

def extraction_node(state: TruthLensState) -> dict:
    logger.info("Extraction node processing phase started.")
    try:
        claim_service = ClaimService()

        transcript = state.get("transcript", "")
        if not transcript:
            raise ValueError("No valid transcript text available in the state context to extract claims from.")

        extracted_claims = claim_service.extract_claims(transcript)
        
        logger.info(f"Successfully extracted {len(extracted_claims)} verifiable claims from the transcript.")

        # CRITICAL FIX: Return ONLY the updated claims key
        return {"claims": extracted_claims}

    except Exception as node_error:
        error_msg = f"Fatal system interruption in extraction node: {str(node_error)}"
        logger.error(error_msg)
        return {"error": error_msg}