# class SearchService:
#     def __init__(self, api_key=None):
#         self.api_key = api_key  # for SerpAPI, Tavily, etc.

#     def search_evidence(self, claims: list) -> dict:
#         """
#         Input: claims (list[str])
#         Output: dictionary mapping claim -> list of evidence URLs
#         Example: 
#         {
#             "5G causes cancer": ["https://trusted-source1.com", "https://trusted-source2.com"],
#             "NASA confirmed aliens": ["https://trusted-source3.com"]
#         }
#         """
#         results = {}
#         for claim in claims:
#             results[claim] = ["https://trusted-source.com"]
#         return results
    
#     Input: claims (list of strings)
# Output: search_results (dict of claim -> list of URLs)

"""
Search Service Module

This module provides a SearchService class that takes a list of textual claims
and queries the Tavily API to find relevant web evidence. It uses concurrent
threading to process multiple claims simultaneously for faster execution.
"""

import os 
import logging 
from typing import List, Dict 
from concurrent.futures import ThreadPoolExecutor, as_completed 
from tavily import TavilyClient 

from dotenv import load_dotenv
load_dotenv()

# Set up logging for this module
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
          raise ValueError("TAVILY_API_KEY is not set. Please provide it as an argument or set the environment variable.")
      
      self.client = TavilyClient(api_key=self.api_key)

  def _search_single_claim(self, claim: str) -> dict: 
      """
      Private worker method to handle the Tavily API call for a single claim.

      Input: 
          claim (str): A single string representing the claim to search for.
                        Example: "5G causes cancer"

      Output: 
          dict: A dictionary containing the original claim and a list of extracted evidence.
                Example:
                {
                    "claim": "5G causes cancer",
                    "evidence": [
                        {
                            "title": "Article Title", 
                            "url": "https://trusted-source.com/article", 
                            "snippet": "Relevant text from the article..."
                        }
                    ]
                }
      """
      try: 
          # Make the API request to Tavily
          response = self.client.search(
              query=claim, 
              search_depth='advanced', 
              max_results=3, 
              include_answer=False, 
              include_raw_content=False 
          ) 
          # Extract and format the specific fields we care about
          evidence_list = [ 
              {
                  "title": result.get("title", ""), 
                  "url": result.get("url", ""), 
                  "snippet": result.get("content", "") 
              }
              for result in response.get("results", [])
          ]
          
          return {"claim": claim, "evidence": evidence_list}

      except Exception as e: 
          logger.error(f"Search failed for claim '{claim}': {str(e)}")
          # Return an empty evidence list if the API call fails so the program doesn't crash
          return {"claim": claim, "evidence": []}

  def search_evidence(self, claims: List[str]) -> Dict[str, List[Dict[str, str]]]: 
      """
      Public method to search multiple claims concurrently.

      Input: 
          claims (list[str]): A list of string claims to be fact-checked.
                              Example: ["5G causes cancer", "NASA confirmed aliens"]

      Output: 
          dict: A dictionary mapping each claim (key) to a list of evidence dictionaries (value).
                Example: 
                {
                    "5G causes cancer": [
                        {"title": "...", "url": "https://trusted-source1.com", "snippet": "..."},
                        {"title": "...", "url": "https://trusted-source2.com", "snippet": "..."}
                    ],
                    "NASA confirmed aliens": [
                        {"title": "...", "url": "https://trusted-source3.com", "snippet": "..."}
                    ]
                }
      """
      logger.info(f"Starting search for {len(claims)} claims.")
      results = {} 

      # Use a ThreadPoolExecutor to run multiple API calls at the same time
      with ThreadPoolExecutor() as executor: 
          # Dictionary comprehension to map the future execution to its specific claim
          future_to_claim = {
              executor.submit(self._search_single_claim, claim): claim 
              for claim in claims 
          }

          # Gather the results as each thread finishes its API call
          for future in as_completed(future_to_claim): 
              result_data = future.result() 
              
              # Extract the formatted data from the private method's output
              claim = result_data["claim"]
              evidence = result_data["evidence"]

              # Populate the final results dictionary
              results[claim] = evidence

      return results


if __name__ == "__main__": 
    search = SearchService()
    claims=["Obsession is not a good movie", "Weapons is not a good movie"] 
    results = search.search_evidence(claims=claims)
    print(results)