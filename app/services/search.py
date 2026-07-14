"""
Search Service Module

This module provides a SearchService class that takes a list of textual claims
and queries the Tavily API to find relevant web evidence. It uses concurrent
threading to process multiple claims simultaneously for faster execution.
"""

import os 
import logging 
import sys
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed 
from tavily import TavilyClient 
from dotenv import load_dotenv

# Load local environment configurations
load_dotenv()

# Set up logging using standard module-level resolution
logger = logging.getLogger(__name__)


class SearchService: 
    """
    A service class to search for evidence related to specific claims using the Tavily API.
    """

    def __init__(self, api_key: str = None): 
        """
        Initializes the SearchService with a Tavily API key.

        Args:
            api_key (str, optional): The Tavily API key. If not provided, the class 
                                     will attempt to load it from the 'TAVILY_API_KEY' 
                                     environment variable.
        Raises:
            ValueError: If no API key is provided and the environment variable is not set.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key: 
            raise ValueError(
                "TAVILY_API_KEY is not set. Please provide it as an argument or set the environment variable."
            )
        
        self.client = TavilyClient(api_key=self.api_key)
        logger.info("SearchService successfully initialized.")

    def _search_single_claim(self, claim: str) -> Dict[str, Any]: 
        """
        Private worker method to handle the Tavily API call for a single claim.

        Args:
            claim (str): A single string representing the claim query to search for.

        Returns:
            Dict[str, Any]: A dictionary containing the original claim string and a formatted 
                            list of extracted evidence objects.
        """
        try: 
            # Make the advanced structural API request to Tavily
            response = self.client.search(
                query=claim, 
                search_depth="advanced", 
                max_results=3, 
                include_answer=True,
                include_raw_content=False 
            ) 
            
            # Extract and format the specific field strings we need for extraction matching
            evidence_list = [ 
                {
                    "title": result.get("title", ""), 
                    "url": result.get("url", ""), 
                    "snippet": result.get("content", "") 
                }
                for result in response.get("results", [])
            ]
            
            logger.info(f"Retrieved {len(evidence_list)} web evidence snippets for claim query: '{claim}'")
            return {"claim": claim, "evidence": evidence_list}

        except Exception as e: 
            logger.error(f"Tavily search execution failed for claim query '{claim}': {str(e)}")
            # Return an empty evidence list if the API call fails so the pipeline doesn't crash
            return {"claim": claim, "evidence": []}

    def search_evidence(self, claims: List[str]) -> Dict[str, List[Dict[str, str]]]: 
        """
        Public endpoint method to search multiple claims concurrently using thread pooling.

        Args:
            claims (List[str]): A list of string claims to be fact-checked.

        Returns:
            Dict[str, List[Dict[str, str]]]: A dictionary mapping each claim query string (key) 
                                             to a list of snippet dictionaries (value).
        """
        if not claims:
            logger.warning("No claims passed to search execution pipeline.")
            return {}

        logger.info(f"Starting concurrent search operations for {len(claims)} claim query lines.")
        results = {} 

        # Cap max_workers at 3 to align with upstream transcript limits and avoid rate-limiting throttling
        with ThreadPoolExecutor(max_workers=3) as executor: 
            # Map the execution task thread to its respective key string
            future_to_claim = {
                executor.submit(self._search_single_claim, claim): claim 
                for claim in claims 
            }

            # Gather and register the results array contents as each worker thread checks back in
            for future in as_completed(future_to_claim): 
                result_data = future.result() 
                
                claim = result_data["claim"]
                evidence = result_data["evidence"]

                # Populate the final results dictionary mapping matrix
                results[claim] = evidence

        logger.info(f"Completed search worker pipeline loop for all {len(claims)} items.")
        return results


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

    print("\n--- Testing Tavily Search Service ---")
    
    try:
        search = SearchService()
        test_claims = ["Obsession is not a good movie", "Weapons is not a good movie"] 
        
        results = search.search_evidence(claims=test_claims)
        
        print("\n--- Raw Search Service Output JSON ---")
        import json
        print(json.dumps(results, indent=4))
        print("\n✅ Search Service validation trace complete.\n")
        
    except Exception as err:
        print(f"\n❌ Service test execution failed: {err}\n")