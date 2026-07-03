import os
import json
import logging
from typing import List, Dict
from groq import Groq

# Set up logging using the python file's name dynamically
logger = logging.getLogger(__name__)


class ClaimService:
    """
    Service to extract factual, verifiable claims from transcripts using Groq's high-speed LLMs.
    """
    def __init__(self, api_key: str = None, model: str = "llama-3.1-8b-instant"):
        """
        Initializes the ClaimService with a Groq API key and model choice.
        
        Args:
            api_key: Your Groq API key. Defaults to the GROQ_API_KEY env variable.
            model: The Groq model to use. Llama 3 70B is recommended for accuracy on data extraction.
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please provide it or set the environment variable.")
        
        self.client = Groq(api_key=self.api_key)

    def extract_claims(self, transcript: str) -> List[str]:
        """
        Input: transcript text (str)
        Output: list of claim strings (list[str])
        
        Extracts a simple, flat list of claims from the transcript.
        """
        logger.info(f"Extracting basic claims using Groq ({self.model})...")
        
        if not transcript.strip():
            return []

        # For Groq's JSON mode to work, the word "JSON" MUST be in the prompt.
        prompt = f"""
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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert fact-checking assistant."},
                    {"role": "user", "content": prompt}
                ],
                # Force Groq to return a valid JSON object
                response_format={"type": "json_object"},
                temperature=0.1 # Low temperature for more deterministic, factual extraction
            )
            
            raw_content = response.choices[0].message.content
            parsed_json = json.loads(raw_content)
            
            return parsed_json.get("claims", [])
                
        except Exception as e:
            logger.error(f"Failed to extract claims: {str(e)}")
            return []

    def extract_structured_claims(self, transcript: str) -> List[Dict[str, str]]:
        """
        Input: transcript text (str)
        Output: list of dictionaries with 'text' and 'timestamp' keys.
        
        Extracts claims along with their timestamps.
        """
        logger.info(f"Extracting structured claims with timestamps using Groq ({self.model})...")
        
        if not transcript.strip():
            return []

        prompt = f"""
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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert fact-checking assistant."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            raw_content = response.choices[0].message.content
            parsed_json = json.loads(raw_content)
            
            return parsed_json.get("claims", [])

        except Exception as e:
            logger.error(f"Failed to extract structured claims: {str(e)}")
            return []


# ==========================================
# Example Usage:
# ==========================================
if __name__ == "__main__":
    # Mock transcript with timestamps
    sample_transcript = """
    [00:10] Host: Welcome back to the show.
    [00:31] Guest: Thanks for having me. Did you know that 5G causes cancer? It's true.
    [01:12] Guest: Also, just last week, NASA confirmed aliens exist on Mars. 
    [01:25] Host: That's wild. Let's take a break.
    """
    
    # Initialize the service (ensure your GROQ_API_KEY is in your environment)
    # To run this for real, replace the string below with your actual API key or leave it empty to read from environment variables.
    service = ClaimService(api_key="gsk_mock_key_do_not_actually_run_this_without_real_key")
    
    # Test the basic extraction
    basic_claims = service.extract_claims(sample_transcript)
    print("Basic Claims:", basic_claims)
    
    # Test the structured extraction
    structured_claims = service.extract_structured_claims(sample_transcript)
    print("Structured Claims:", json.dumps(structured_claims, indent=4))