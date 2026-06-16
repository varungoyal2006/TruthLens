```python
"""
Transcript Service Module

This service converts downloaded audio/video files into text transcripts
using Groq's Whisper model.

Workflow:
    Video/Audio File
            ↓
    Groq Whisper API
            ↓
       Transcript
"""

import os
import logging
from typing import Dict

from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)


class TranscriptService:
    """
    Service class for transcript extraction using Groq Whisper.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize Groq client.

        Args:
            api_key (str, optional):
                Groq API key.
                Defaults to GROQ_API_KEY from environment.
        """

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Please add it to your .env file."
            )

        self.client = Groq(api_key=self.api_key)

    def extract_transcript(
        self,
        video_path: str
    ) -> Dict[str, str]:
        """
        Extract transcript from an audio/video file.

        Args:
            video_path (str):
                Local path of downloaded video/audio file.

        Returns:
            dict:
            {
                "status": "success",
                "video_path": "...",
                "transcript": "..."
            }

            OR

            {
                "status": "error",
                "message": "..."
            }
        """

        try:

            logger.info(
                f"Starting transcript extraction: {video_path}"
            )

            if not os.path.exists(video_path):
                raise FileNotFoundError(
                    f"File not found: {video_path}"
                )

            with open(video_path, "rb") as media_file:

                transcription = (
                    self.client.audio.transcriptions.create(
                        file=media_file,
                        model="whisper-large-v3"
                    )
                )

            transcript_text = transcription.text

            logger.info(
                "Transcript extraction completed successfully."
            )

            return {
                "status": "success",
                "video_path": video_path,
                "transcript": transcript_text
            }

        except Exception as error:

            logger.error(
                f"Transcript extraction failed: {str(error)}"
            )

            return {
                "status": "error",
                "message": str(error)
            }


# ==========================================
# Example Usage
# ==========================================

if __name__ == "__main__":

    service = TranscriptService()

    result = service.extract_transcript(
        "temp.mp4"
    )

    print(result)
```
