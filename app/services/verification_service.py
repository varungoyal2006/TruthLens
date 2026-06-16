```python
"""
Verification Service Module

Uses Groq LLMs to verify extracted claims against
retrieved evidence from Tavily.

Workflow:

Claim
   +
Evidence
   ↓
Groq LLM
   ↓
Verdict
Confidence
Reasoning
"""

import os
import json
import logging
from typing import Dict

from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)


class VerificationService:
    """
    Service responsible for fact-checking claims
    using retrieved evidence.
    """

    def __init__(
        self,
        api_key: str = None,
        model: str = "llama3-70b-8192"
    ):
        """
        Initialize Groq client.

        Args:
            api_key (str, optional):
                Groq API key.
            model (str):
                Groq model used for verification.
        """

        self.api_key = api_key or os.getenv(
            "GROQ_API_KEY"
        )

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Please add it to your .env file."
            )

        self.client = Groq(
            api_key=self.api_key
        )

        self.model = model

    def verify_claim(
        self,
        claim: str,
        evidence: str
    ) -> Dict:
        """
        Verify a claim using evidence.

        Args:
            claim (str):
                Extracted claim.

            evidence (str):
                Evidence text collected
                from Tavily search results.

        Returns:
            {
                "status": "success",
                "claim": "...",
                "evidence": "...",
                "verdict": "...",
                "confidence": "...",
                "reasoning": "..."
            }
        """

        try:

            logger.info(
                f"Starting verification for claim: {claim}"
            )

            prompt = f"""
You are an expert fact-checking assistant.

Claim:
{claim}

Evidence:
{evidence}

Analyze the evidence and determine whether the claim is:

- TRUE
- FALSE
- PARTIALLY TRUE
- UNSUPPORTED

Return ONLY valid JSON.

Example:

{{
    "verdict": "FALSE",
    "confidence": 92,
    "reasoning": "The evidence contradicts the claim."
}}
"""

            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content":
                            "You are an expert fact-checker."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={
                        "type": "json_object"
                    },
                    temperature=0.1
                )
            )

            raw_content = (
                response
                .choices[0]
                .message
                .content
            )

            parsed_json = json.loads(
                raw_content
            )

            logger.info(
                "Verification completed successfully."
            )

            return {
                "status": "success",
                "claim": claim,
                "evidence": evidence,
                "verdict": parsed_json.get(
                    "verdict",
                    "UNSUPPORTED"
                ),
                "confidence": str(
                    parsed_json.get(
                        "confidence",
                        0
                    )
                ),
                "reasoning": parsed_json.get(
                    "reasoning",
                    "No reasoning provided."
                )
            }

        except Exception as error:

            logger.error(
                f"Verification failed: {str(error)}"
            )

            return {
                "status": "error",
                "message": str(error)
            }


# ==========================================
# Example Usage
# ==========================================

if __name__ == "__main__":

    service = VerificationService()

    claim = "NASA confirmed aliens."

    evidence = """
    NASA has released no official statement
    confirming the existence of aliens.
    """

    result = service.verify_claim(
        claim,
        evidence
    )

    print(result)
```
