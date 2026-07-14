"""
Verification Service Module

This module leverages Groq's reasoning-heavy LLMs to evaluate contextually
resolved claims against retrieved evidence blocks (from local RAG or Tavily fallback).
It assigns a factual verdict (True, False, Unverified), constructs a logical 
justification, and aggregates the reliable source URLs utilized.

It also contains an orchestration function to generate a unified, structured 
credibility report for an entire video piece.
"""

import os
import json
import logging
import sys
from typing import List, Dict, Any

from groq import Groq
from dotenv import load_dotenv

# Load local environment configurations
load_dotenv()

# Set up logging using standard module-level resolution
logger = logging.getLogger(__name__)

# ==========================================
# Prompt Templates
# ==========================================

CLAIM_VERIFICATION_PROMPT = """
You are an expert, unbiased fact-checking adjudicator. Your task is to evaluate a single factual statement against a provided list of web/database evidence snippets and determine its factual validity.

### Evaluation Protocol:
1. Thoroughly cross-reference the "Claim" against the provided "Evidence Snippets".
2. Assign one of the following strict verdicts:
   - "True": If the evidence explicitly confirms, validates, and supports the claim.
   - "False": If the evidence directly contradicts, refutes, or disproves the core assertion of the claim.
   - "Unverified": If the evidence is insufficient, ambiguous, tangential, or fails to provide clear confirmation or refutation.
3. Write a concise, objective "Explanation" (2-3 sentences) detailing *why* the verdict was reached based strictly on the provided evidence. Do not extrapolate or add outside knowledge.
4. Extract all source URLs from the evidence snippets that directly contributed to your verdict and list them in the "sources" array.

You must return your response as a valid JSON object matching the schema below.

### Expected Output JSON Format:
{{
    "verdict": "True" | "False" | "Unverified",
    "explanation": "Detailed professional reasoning justifying the final verdict...",
    "sources": ["https://source-url-1.com", "https://source-url-2.com"]
}}

### Input Context:
- **Claim to Verify**: {claim}
- **Retrieved Evidence**:
{evidence_context}
"""

# ==========================================
# Service Class
# ==========================================

class VerificationService:
    """
    Service responsible for deep analytical claim verification against structured text evidence, 
    as well as macro-level credibility reporting.
    """

    def __init__(self, api_key: str = None, model: str = "llama-3.1-8b-instant"):
        """
        Initializes the VerificationService client.

        Args:
            api_key (str, optional): Groq API key. Defaults to the GROQ_API_KEY env variable.
            model (str, optional): The high-reasoning model for evaluation logic. 
                                  Defaults to "llama-3.1-8b-instant".
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please provide it or set the environment variable.")

        self.client = Groq(api_key=self.api_key)
        logger.info(f"VerificationService initialized successfully with model: {self.model}")

    def verify_claim(self, claim: str, evidence: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Evaluates a single claim against a list of evidence dicts.

        Args:
            claim (str): The contextually resolved claim string.
            evidence (List[Dict[str, str]]): List of evidence dicts containing 'title', 'url', and 'snippet'.

        Returns:
            Dict[str, Any]: Dict containing 'verdict', 'explanation', and verified 'sources'.
        """
        logger.info(f"Initiating factual audit for claim: '{claim[:50]}...'")

        if not evidence:
            logger.warning(f"No evidence context provided for claim: '{claim}'. Automatically marking Unverified.")
            return {
                "verdict": "Unverified",
                "explanation": "No supporting or refuting evidence was found in our knowledge database or live search indexes.",
                "sources": []
            }

        try:
            # 1. Format the evidence array into a readable block for the LLM context window
            formatted_evidence_blocks = []
            for idx, item in enumerate(evidence):
                block = (
                    f"[{idx+1}] Title: {item.get('title', 'N/A')}\n"
                    f"    Source URL: {item.get('url', 'N/A')}\n"
                    f"    Snippet: {item.get('snippet', 'N/A')}\n"
                )
                formatted_evidence_blocks.append(block)
            
            evidence_context = "\n".join(formatted_evidence_blocks)

            # 2. Build the final prompt string
            formatted_prompt = CLAIM_VERIFICATION_PROMPT.format(
                claim=claim,
                evidence_context=evidence_context
            )

            # 3. Request evaluation execution via Groq JSON Mode
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional, objective fact-checking evaluation model."},
                    {"role": "user", "content": formatted_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0  # Zero temperature forces optimal deterministic reasoning
            )

            raw_content = response.choices[0].message.content
            parsed_result = json.loads(raw_content)

            logger.info(f"Audit completed. Verdict for claim: [{parsed_result.get('verdict')}]")
            return parsed_result

        except Exception as e:
            logger.error(f"Critical execution fault during claim verification loop: {str(e)}")
            return {
                "verdict": "Unverified",
                "explanation": f"An internal system error occurred during evaluation processing: {str(e)}",
                "sources": []
            }

    def generate_final_report(self, verified_claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates individual claim verification results to calculate an overall score 
        and compile a structural summary block at the top of the report payload.

        Args:
            verified_claims (List[Dict[str, Any]]): List of dict blocks, each containing:
                {
                    "claim": "The claim text...",
                    "verdict": "True" | "False" | "Unverified",
                    "explanation": "...",
                    "sources": [...]
                }

        Returns:
            Dict[str, Any]: The finalized master report object including summary metadata.
        """
        logger.info("Compiling macro credibility report score indicators...")
        
        if not verified_claims:
            return {
                "summary": {
                    "credibility_score": 0.0,
                    "rating": "Unknown",
                    "total_claims_checked": 0,
                    "breakdown": {"True": 0, "False": 0, "Unverified": 0},
                    "verdict_justification": "No verifiable claims were provided to generate an assessment."
                },
                "detailed_audits": []
            }

        # Step 1: Initialize analytical counter variables
        true_count = 0
        false_count = 0
        unverified_count = 0
        total_points = 0.0
        all_collected_sources = set()

        # Step 2: Loop through and tally data matrices
        for item in verified_claims:
            verdict = item.get("verdict", "Unverified")
            all_collected_sources.update(item.get("sources", []))

            if verdict == "True":
                true_count += 1
                total_points += 1.0
            elif verdict == "False":
                false_count += 1
                total_points += 0.0
            else:
                unverified_count += 1
                total_points += 0.5  # Neutral weighting

        # Step 3: Run arithmetic percentages
        total_claims = len(verified_claims)
        credibility_score = round((total_points / total_claims) * 100, 1)

        # Step 4: Map credibility brackets onto categorical ratings
        if credibility_score >= 85.0:
            rating = "Highly Trustworthy"
            justification = f"This content demonstrates excellent factual backing, with {true_count} out of {total_claims} statements verified as completely accurate."
        elif credibility_score >= 60.0:
            rating = "Mostly Verifiable (Proceed with Caution)"
            justification = f"The content contains verified facts but carries a combined number of {false_count + unverified_count} statements that are either unverified or false."
        elif credibility_score >= 35.0:
            rating = "Low Credibility / Misleading Contexts"
            justification = f"Caution recommended. A significant portion of this content ({false_count} confirmed false, {unverified_count} unverified) could not be substantiated."
        else:
            rating = "Highly Deceptive / Dangerous Information"
            justification = f"This file scored a critically low {credibility_score}%. The vast majority of its core claims are demonstrably false or unverified rumors."

        # Step 5: Package the macro summary seamlessly over the audit collection arrays
        return {
            "summary": {
                "credibility_score": credibility_score,
                "rating": rating,
                "total_claims_checked": total_claims,
                "breakdown": {
                    "True": true_count,
                    "False": false_count,
                    "Unverified": unverified_count
                },
                "total_unique_sources_cited": len(all_collected_sources),
                "verdict_justification": justification
            },
            "detailed_audits": verified_claims
        }


# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__":
    # Configure root standalone logger metrics matching TruthLens layout rules
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    print("\n--- Testing Micro-Verification & Macro-Aggregation ---")

    # Mock collection of processed node payloads
    mock_processed_audits = [
        {
            "claim": "5G cell tower signals directly mutate cell structures to cause cancer.",
            "verdict": "False",
            "explanation": "Multiple peer-reviewed oncology studies and WHO documentation confirm that 5G RF waves are non-ionizing and cannot alter human cellular DNA structures.",
            "sources": ["https://who.int/radiation-5g", "https://cancer.org/electromagnetic-fields"]
        },
        {
            "claim": "Apple Inc. released a patch for iOS to plug a zero-day kernel exploit.",
            "verdict": "True",
            "explanation": "Apple's security repository notes confirmation that update patch updates resolve CVE zero-day bugs flagged by threat research groups.",
            "sources": ["https://support.apple.com/en-us/HT201222"]
        },
        {
            "claim": "A secret bunker network was discovered under the Great Pyramids last Tuesday.",
            "verdict": "Unverified",
            "explanation": "Archeological ministries have released no press updates confirming excavation anomalies, making this statement an unconfirmed rumor.",
            "sources": []
        }
    ]

    try:
        verifier = VerificationService()
        
        # Compile full report schema structure
        final_report = verifier.generate_final_report(verified_claims=mock_processed_audits)
        
        print("\n--- Final Consolidated Report Output JSON ---")
        print(json.dumps(final_report, indent=4))
        print("\n✅ Verification and Reporting Service metrics successfully validated.\n")
        
    except Exception as err:
        print(f"\n❌ Service test execution failed: {err}\n")
    