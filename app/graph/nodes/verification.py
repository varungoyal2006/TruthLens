import logging
from app.graph.state import TruthLensState
from app.services.verification import VerificationService

logger = logging.getLogger(__name__)

def verification_node(state: TruthLensState) -> dict:
    logger.info("Verification node processing phase started.")
    try:
        verifier = VerificationService()
        
        claims = state.get("claims", [])
        evidence_data = state.get("evidence_data", {})

        if not claims:
            logger.warning("No claims staged in state context. Generating empty structural report.")
            return {"final_report": verifier.generate_final_report([])}

        verified_claims_list = []

        for claim_obj in claims:
            claim_text = claim_obj.get("claim", "")
            if not claim_text:
                continue

            associated_evidence = evidence_data.get(claim_text, [])
            audit_payload = verifier.verify_claim(claim=claim_text, evidence=associated_evidence)

            completed_audit = {
                "claim": claim_text,
                "verdict": audit_payload.get("verdict", "Unverified"),
                "explanation": audit_payload.get("explanation", "System error processing statement reasoning."),
                "sources": audit_payload.get("sources", [])
            }
            verified_claims_list.append(completed_audit)

        master_report = verifier.generate_final_report(verified_claims=verified_claims_list)
        master_report["summary"]["sourcing_traces"] = state.get("evidence_sources", {})

        logger.info(f"Unified credibility report successfully compiled. Global Score: {master_report['summary']['credibility_score']}%")

        # CRITICAL FIX: Return ONLY the final compiled report key
        return {"final_report": master_report}

    except Exception as node_error:
        error_msg = f"Fatal system interruption in verification node: {str(node_error)}"
        logger.error(error_msg)
        return {"error": error_msg}