```python
"""
YouTube Service Module

This module provides functionality for:

1. Validating YouTube URLs
2. Fetching video metadata
3. Downloading audio for transcript generation

Workflow:

YouTube URL
      ↓
YoutubeService
      ↓
audio.mp3
      ↓
TranscriptService
      ↓
Groq Whisper
"""

import logging
from typing import Dict, Any

import yt_dlp

logger = logging.getLogger(__name__)


class YoutubeService:
    """
    Service for handling YouTube videos.
    """

    def __init__(self):
        logger.info("YoutubeService initialized.")

    def get_video_info(
        self,
        video_url: str
    ) -> Dict[str, Any]:
        """
        Retrieve video metadata without downloading.

        Args:
            video_url (str): YouTube URL

        Returns:
            Dict containing metadata.
        """

        try:

            ydl_opts = {
                "quiet": True,
                "skip_download": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(
                    video_url,
                    download=False
                )

            return {
                "status": "success",
                "title": info.get("title"),
                "channel": info.get("uploader"),
                "duration": info.get("duration"),
                "video_id": info.get("id"),
                "webpage_url": info.get("webpage_url")
            }

        except Exception as error:

            logger.error(
                f"Failed to fetch video info: {str(error)}"
            )

            return {
                "status": "error",
                "message": str(error)
            }

    def download_audio(
        self,
        video_url: str,
        output_path: str = "temp_audio.%(ext)s"
    ) -> Dict[str, str]:
        """
        Download audio from a YouTube video.

        Args:
            video_url (str):
                YouTube URL

            output_path (str):
                Output file template

        Returns:
            {
                "status": "success",
                "video_url": "...",
                "audio_path": "temp_audio.mp3"
            }
        """

        try:

            logger.info(
                f"Starting audio download: {video_url}"
            )

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_path,
                "quiet": True,
                "noplaylist": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192"
                    }
                ]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                ydl.download([video_url])

            audio_file = "temp_audio.mp3"

            logger.info(
                "Audio download completed successfully."
            )

            return {
                "status": "success",
                "video_url": video_url,
                "audio_path": audio_file
            }

        except Exception as error:

            logger.error(
                f"Audio download failed: {str(error)}"
            )

            return {
                "status": "error",
                "message": str(error)
            }


# ==========================================
# Example Usage
# ==========================================

if __name__ == "__main__":

    service = YoutubeService()

    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    info = service.get_video_info(url)

    print(info)

    # result = service.download_audio(url)
    # print(result)
```
