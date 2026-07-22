"""
Claim Extraction Service Module

This module leverages Groq's high-speed LLMs to process raw video 
transcripts and extract factual, verifiable claims. It handles contextual 
resolution (e.g., replacing pronouns with proper nouns) and generates 
optimized search queries for downstream web searching.
"""

import os 
import json 
import logging 
import sys
from typing import List, Dict

from groq import Groq 
from dotenv import load_dotenv 

# Load environment variables
load_dotenv() 

# Initialize logger for this specific module
logger = logging.getLogger(__name__)

# ==========================================
# Prompt Templates
# ==========================================

CLAIM_EXTRACTION_PROMPT = """
Analyze the following transcript and extract the core factual, verifiable claims being made. 
Ignore subjective opinions, conversational banter, greetings, and filler text.

For each extracted claim, you must perform two steps:
1. Contextual Resolution: Rewrite the claim to be entirely self-contained. Replace vague nouns, 
   brand items, or pronouns (e.g., "it", "he", "the sandwich") with their explicit names derived 
   from the transcript context so that the claim makes absolute sense on its own.
2. Search Query Optimization: Create a highly specific, keyword-optimized search engine query 
   designed to find verification evidence. Append explicit anchoring context (like the restaurant, 
   brand, or full industry name) to prevent semantic confusion (e.g., mixing up fast food items with sports/finance).

You must return your response as a valid JSON object containing a single key called "claims" 
which maps to an array of objects.

Example Output:
{{
    "claims": [
        {{
            "claim": "The 'Shaq Attack' chicken sandwich at Big Chicken costs $9.91 after tax.",
            "search_query": "Big Chicken restaurant Shaq Attack sandwich menu price after tax"
        }},
        {{
            "claim": "McDonald's edamame-shaped novelty fries are manufactured to be completely hollow on the inside.",
            "search_query": "McDonalds edamame shaped hollow fries internal texture structure"
        }}
    ]
}}

Transcript:
{transcript}
"""

STRUCTURED_CLAIM_PROMPT = """
Analyze the following transcript. Extract the core verifiable claims being made.
For each claim, provide the exact text of the claim and the timestamp where it occurs.
If no exact timestamp is visible, estimate it or use '00:00'.

You must return your response as a valid JSON object containing a single key called "claims".
This key must map to an array of objects, where each object has a "text" string and a "timestamp" string.

Example Output:
{{
    "claims": [
        {{"text": "5G causes cancer", "timestamp": "00:31"}},
        {{"text": "NASA confirmed aliens", "timestamp": "01:12"}}
    ]
}}

Transcript:
{transcript}
"""

# ==========================================
# Service Class
# ==========================================

class ClaimService: 
    """
    Service to extract factual, verifiable claims from transcripts using Groq's LLMs.
    """

    def __init__(self, api_key: str = None, model: str = "llama-3.1-8b-instant"): 
        """
        Initializes the ClaimService with a Groq API key and model choice.
        
        Args:
            api_key (str, optional): Groq API key. Defaults to the GROQ_API_KEY env variable.
            model (str, optional): The Groq model to use. Defaults to "llama-3.1-8b-instant".
            
        Raises:
            ValueError: If the GROQ_API_KEY is not set.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please provide it or set the environment variable.")

        self.client = Groq(api_key=self.api_key) 
        self.model = model

        logger.info(f"ClaimService initialized with model: {self.model}")

    def extract_claims(self, transcript: str) -> List[Dict[str, str]]: 
        """
        Extracts contextualized claims and generates optimized search queries.
        
        Args:
            transcript (str): The raw text transcript of the video.
            
        Returns:
            List[Dict[str, str]]: A list of dictionaries containing 'claim' and 'search_query'.
        """
        logger.info("Claim extraction has begun.")

        if not transcript.strip(): 
            logger.warning("Empty transcript provided. Returning empty list.")
            return []

        try: 
            formatted_prompt = CLAIM_EXTRACTION_PROMPT.format(transcript=transcript)

            response = self.client.chat.completions.create(
                model=self.model, 
                messages=[
                    {"role": "system", "content": "You are an expert fact-checking assistant."},
                    {"role": "user", "content": formatted_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1            
            )
            
            raw_content = response.choices[0].message.content
            parsed_json = json.loads(raw_content)

            claims = parsed_json.get("claims", [])
            logger.info(f"Successfully extracted {len(claims)} claims.")
            return claims 

        except Exception as e: 
            logger.error(f"Failed to extract claims: {str(e)}")
            return [] 

    def extract_structured_claim(self, transcript: str) -> List[Dict[str, str]]: 
        """
        Extracts claims along with their approximate timestamps.
        
        Args:
            transcript (str): The raw text transcript (preferably with timestamps).
            
        Returns:
            List[Dict[str, str]]: A list of dictionaries with 'text' and 'timestamp' keys.
        """
        try: 
            if not transcript.strip(): 
                logger.warning("Empty transcript provided. Returning empty list.")
                return []

            structured_prompt = STRUCTURED_CLAIM_PROMPT.format(transcript=transcript)
            logger.info("Created the prompt for structured claim extraction.")

            response = self.client.chat.completions.create(
                model=self.model, 
                messages=[
                    {"role": "system", "content": "You are a fact-checking expert. Go through the text and extract verifiable claims."},
                    {"role": "user", "content": structured_prompt}
                ], 
                temperature=0.1, 
                response_format={"type": "json_object"}
            )

            logger.info("Successfully received response from Groq.")

            raw_result = response.choices[0].message.content 
            json_output = json.loads(raw_result)
            
            result = json_output.get("claims", [])
            return result 

        except Exception as e: 
            logger.error(f"The following error occurred during structured extraction: {str(e)}")
            return []


# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__": 
    # Configure logging for local testing
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s - %(name)s - "
            "[%(filename)s:%(lineno)d] - "
            "%(funcName)s() - "
            "%(levelname)s - %(message)s"
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    sample_transcript = """
    [00:10] Host: Welcome back to the show.
    [00:31] Guest: Thanks for having me. Did you know that 5G causes cancer? It's true.
    [01:12] Guest: Also, just last week, NASA confirmed aliens exist on Mars. 
    [01:25] Host: That's wild. Let's take a break.
    """
    
    try:
        cs = ClaimService() 
        
        print("\n--- Structured Timestamp Extraction ---")
        result_structured = cs.extract_structured_claim(transcript=sample_transcript)
        print(json.dumps(result_structured, indent=4))

        print("\n--- Basic Context-Aware Extraction ---")
        result_basic = cs.extract_claims(transcript=sample_transcript)
        print(json.dumps(result_basic, indent=4))
        
    except Exception as e:
        print(f"Service initialization failed (Check API Key): {e}")