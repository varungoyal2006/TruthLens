"""
Embedding Engine Module

Handles turning text query and claim strings into numerical vectors using 
Google's native GenAI SDK for semantic search matching inside ChromaDB.
"""

import os
import logging
from typing import List

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logger using standard module-level resolution
logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Service wrapper for converting claims and queries into high-dimensional 
    vector embeddings using Google's Gemini Embedding model.
    """

    def __init__(self, model: str = "gemini-embedding-001"):
        """
        Initializes the Google GenAI client using environment variables.
        
        Args:
            model (str, optional): The embedding model hosted via Google. 
                                  Defaults to "gemini-embedding-001".
        """
        # Google's SDK natively looks for GEMINI_API_KEY or GOOGLE_API_KEY
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model
        
        if not self.api_key:
            logger.warning("Google API Key not found. Defaulting to dummy mock vector fallback.")
            self.client = None
        else:
            # Initialize the modern unified Google GenAI client
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"EmbeddingEngine successfully initialized Google GenAI client using model: {self.model}")

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a dense vector embedding for a given string.

        Args:
            text (str): The input text to convert.

        Returns:
            List[float]: A list of floats representing the vector space.
                         Truncated to 768 dimensions via MRL configuration to preserve storage.
        """
        # Standalone mock fallback if testing without keys or in offline mode.
        # Hardcoded to 768 dimensions to match our target ChromaDB configuration matrix.
        if not self.client:
            return [0.0] * 768

        try:
            # Clean text input to ensure stable tokenization across systems
            clean_text = text.replace("\n", " ")

            # Generate embeddings via Google's embed_content API
            response = self.client.models.embed_content(
                model=self.model,
                contents=clean_text,
                # Force output to 768 dimensions to save local DB volume space
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            # Google returns a list of embedding objects; extract the values array
            return response.embeddings[0].values
            
        except Exception as e:
            logger.error(f"Failed to generate embedding vector via Google API: {str(e)}")
            raise e


# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__":
    import sys
    
    # Configure standalone logger format matching app requirements
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    try:
        engine = EmbeddingEngine()
        test_text = "TruthLens dynamic Google RAG routing engine verification loop."
        
        vector = engine.get_embedding(test_text)
        print(f"\n✅ Success! Google embedding generated.")
        print(f"Vector Dimension Count: {len(vector)}")
        print(f"Sample preview (First 5 values): {vector[:5]}\n")
        
    except Exception as err:
        print(f"\n❌ Execution testing failed: {err}\n")