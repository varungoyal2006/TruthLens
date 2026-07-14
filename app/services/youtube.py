"""
YouTube Service Module

This module provides functionality for interacting with YouTube, including:
1. Fetching video metadata without downloading.
2. Downloading audio tracks and automatically bypassing with local files if available.
3. Splitting large audio files into smaller chunks (via ffmpeg) for LLM processing limits.
4. Cleaning up ephemeral audio chunks after processing.
"""

import os
import logging
import subprocess
import yt_dlp
import sys
from typing import Dict, Any, List

# Initialize logger for this specific module
logger = logging.getLogger(__name__)

# Constants for audio processing
DEFAULT_CHUNK_SECONDS = 600

# Path resolution for the 12-Factor App structure
PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
AUDIO_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "tmp", "audio_chunks")
DEFAULT_SECRETS_DIR = os.path.join(PROJECT_ROOT, "tmp", "secrets")


class YoutubeService:
    """
    A service class to handle YouTube metadata extraction, audio downloading, 
    and ffmpeg-based chunking for downstream transcription pipelines.
    """

    def __init__(self):
        """Initializes the YoutubeService and logs the instantiation."""
        logger.info("YoutubeService initialized.")

    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Retrieves the metadata of a YouTube video without downloading the actual content.

        Args:
            video_url (str): The standard URL of the YouTube video.

        Returns:
            Dict[str, Any]: A dictionary containing the extraction status and video details 
                            (title, channel, duration, video_id, webpage_url).
        """
        try:
            ydl_params = {
                "quiet": True,
                "skip_download": True
            }

            with yt_dlp.YoutubeDL(ydl_params) as ydl:
                info = ydl.extract_info(video_url, download=False)

            return {
                "status": "success",
                "title": info.get("title"),
                "channel": info.get("uploader"),
                "duration": info.get("duration"),
                "video_id": info.get("id"),
                "webpage_url": info.get("webpage_url")
            }

        except Exception as error:
            logger.error(f"Failed to fetch video info: {str(error)}")
            return {
                "status": "error",
                "message": str(error)
            }

    def download_audio_chunks(
        self, 
        video_url: str, 
        chunk_seconds: int = DEFAULT_CHUNK_SECONDS, 
        output_dir: str = AUDIO_OUTPUT_DIR
    ) -> Dict[str, Any]:
        """
        Downloads the best available audio from a YouTube video and splits it into smaller chunks using ffmpeg.
        If a file named 'full_audio.mp3' already exists in the output directory, the yt-dlp download 
        is bypassed and the existing file is split instead.

        Args:
            video_url (str): The URL of the YouTube video.
            chunk_seconds (int, optional): The length of each split audio chunk in seconds. Defaults to 600.
            output_dir (str, optional): The directory where audio chunks should be saved. Defaults to AUDIO_OUTPUT_DIR.

        Returns:
            Dict[str, Any]: A dictionary containing the status, the original video URL, 
                            and a list of absolute paths to the generated audio chunks.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # The base name for yt-dlp (NO EXTENSION)
        base_dl_path = os.path.join(output_dir, "full_audio")
        # The final expected file AFTER ffmpeg post-processing adds the extension
        final_mp3_path = f"{base_dl_path}.mp3"

        try:
            # Step 1: Download or Bypass using the FINAL .mp3 path check
            if os.path.exists(final_mp3_path):
                logger.info(f"🚀 Manual bypass: Found existing audio at {final_mp3_path}. Skipping download.")
            else:
                cookies_path = os.path.join(DEFAULT_SECRETS_DIR, "youtube_cookies.txt")
                logger.info(f"Downloading audio for URL: {video_url}")

                yt_dlp_params = {
                    "format": "bestaudio/best",
                    "outtmpl": base_dl_path,  # Passed without .mp3 so the postprocessor appends it cleanly
                    "quiet": False,
                    "noplaylist": True,
                    "cookiefile": cookies_path if os.path.exists(cookies_path) else None,
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    },
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128"
                    }]
                }

                with yt_dlp.YoutubeDL(yt_dlp_params) as ydl:
                    ydl.download([video_url])

            # Ensure the final .mp3 file actually exists before attempting to split
            if not os.path.exists(final_mp3_path):
                raise FileNotFoundError(f"Expected full audio at {final_mp3_path} but file was not found.")

            # Step 2: Split the audio into chunks using ffmpeg
            chunk_pattern = os.path.join(output_dir, "chunk_%03d.mp3")
            logger.info(f"Splitting the audio into {chunk_seconds}s chunks...")

            split_cmd = [
                "ffmpeg",
                "-y",
                "-i", final_mp3_path,
                "-f", "segment",
                "-segment_time", str(chunk_seconds),
                "-c", "copy",
                "-reset_timestamps", "1",
                chunk_pattern
            ]

            result = subprocess.run(split_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg split failed:\n{result.stderr}")

            # Step 3: Collect the generated chunk paths
            chunk_paths: List[str] = sorted(
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if (f.startswith("chunk_") and f.endswith(".mp3"))
            )

            if not chunk_paths:
                raise RuntimeError("ffmpeg ran without error but produced no chunk files.")

            logger.info(
                f"Audio split into {len(chunk_paths)} chunks(s): " +
                ", ".join(os.path.basename(p) for p in chunk_paths)
            )

            # Step 4: Cleanup the large source file to save space
            os.remove(final_mp3_path)
            logger.info("Removed full audio file after chunking.")

            return {
                "status": "success",
                "video_url": video_url,
                "chunk_paths": chunk_paths
            }

        except Exception as error:
            logger.error(f"Failed to download or chunk the video: {str(error)}")
            return {
                "status": "error",
                "message": str(error)
            }

    def cleanup_chunks(self, output_dir: str = AUDIO_OUTPUT_DIR) -> None:
        """
        Deletes all temporary mp3 chunk files from the specified output directory.
        Should be called after the TranscriptService has finished transcribing.

        Args:
            output_dir (str, optional): The directory to clean up. Defaults to AUDIO_OUTPUT_DIR.
        """
        count = 0
        if not os.path.exists(output_dir):
            return
            
        for file in os.listdir(output_dir):
            if file.startswith("chunk_") and file.endswith(".mp3"):
                os.remove(os.path.join(output_dir, file))
                count += 1

        logger.info(f"Cleanup complete. Total chunks removed: {count}")


def setup_logging():
    """
    Configures the root logger for the entire application, establishing a standard 
    format that includes timestamps, file locations, line numbers, and function names.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__":
    setup_logging()
    
    yt = YoutubeService()
    
    # Test metadata fetching
    info = yt.get_video_info(video_url="https://www.youtube.com/watch?v=Y3EPQcWiXF8")
    print("Metadata Output:", info, "\n\n")
    
    # Test downloading and chunking
    result = yt.download_audio_chunks(video_url="https://www.youtube.com/watch?v=Y3EPQcWiXF8")
    print("Chunking Output:", result)
    
    # Optional: Test cleanup (Uncomment to test)
    # yt.cleanup_chunks()