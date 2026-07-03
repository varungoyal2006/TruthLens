"""
YouTube Service Module

This module provides functionality for:

1. Validating YouTube URLs
2. Fetching video metadata
3. Downloading audio for transcript generation
4. Splitting long audio into chunks for Groq Whisper (25MB limit)

Workflow:

YouTube URL
      ↓
YoutubeService
      ↓
audio.mp3  ──(if long)──►  [chunk_0.mp3, chunk_1.mp3, ...]
      ↓
TranscriptService
      ↓
Groq Whisper
"""

import os
import logging
import subprocess
from typing import Dict, Any, List

import yt_dlp

logger = logging.getLogger(__name__)

# Groq Whisper hard limit is 25 MB.
# We target 10-minute chunks (~10 MB at 128kbps) to stay well under it.
DEFAULT_CHUNK_SECONDS = 600   # 10 minutes
DEFAULT_OUTPUT_DIR    = "audio_chunks"


class YoutubeService:
    """
    Service for handling YouTube videos.
    """

    def __init__(self):
        logger.info("YoutubeService initialized.")

    # ------------------------------------------------------------------
    # Public: video metadata
    # ------------------------------------------------------------------

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
                "status":      "success",
                "title":       info.get("title"),
                "channel":     info.get("uploader"),
                "duration":    info.get("duration"),
                "video_id":    info.get("id"),
                "webpage_url": info.get("webpage_url")
            }

        except Exception as error:

            logger.error(
                f"Failed to fetch video info: {str(error)}"
            )

            return {
                "status":  "error",
                "message": str(error)
            }

    # ------------------------------------------------------------------
    # Public: download full audio (kept for short videos / backwards compat)
    # ------------------------------------------------------------------

    def download_audio(
        self,
        video_url: str,
        output_path: str = "temp_audio.%(ext)s"
    ) -> Dict[str, str]:
        """
        Download audio from a YouTube video as a single MP3.

        For videos longer than ~10 minutes prefer download_audio_chunks()
        to stay within Groq Whisper's 25 MB file-size limit.

        Args:
            video_url (str):   YouTube URL
            output_path (str): yt-dlp output template

        Returns:
            {
                "status":     "success",
                "video_url":  "...",
                "audio_path": "temp_audio.mp3"
            }
        """

        try:

            logger.info(
                f"Starting audio download: {video_url}"
            )

            ydl_opts = {
                "format":     "bestaudio/best",
                "outtmpl":    output_path,
                "quiet":      True,
                "noplaylist": True,
                "postprocessors": [
                    {
                        "key":              "FFmpegExtractAudio",
                        "preferredcodec":   "mp3",
                        "preferredquality": "128"
                    }
                ]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            audio_file = "temp_audio.mp3"

            logger.info("Audio download completed successfully.")

            return {
                "status":     "success",
                "video_url":  video_url,
                "audio_path": audio_file
            }

        except Exception as error:

            logger.error(f"Audio download failed: {str(error)}")

            return {
                "status":  "error",
                "message": str(error)
            }

    # ------------------------------------------------------------------
    # Public: download + split into chunks  ← NEW
    # ------------------------------------------------------------------

    def download_audio_chunks(
        self,
        video_url: str,
        chunk_seconds: int = DEFAULT_CHUNK_SECONDS,
        output_dir: str   = DEFAULT_OUTPUT_DIR
    ) -> Dict[str, Any]:
        """
        Download a YouTube video's audio and split it into fixed-length
        MP3 chunks so each file stays under Groq Whisper's 25 MB limit.

        Steps:
            1. Download the full audio as a single MP3 via yt-dlp.
            2. Use ffmpeg to split it into <chunk_seconds>-long segments.
            3. Delete the full MP3 (only chunks are kept).

        Args:
            video_url     (str): YouTube URL.
            chunk_seconds (int): Length of each chunk in seconds (default 600 = 10 min).
            output_dir    (str): Directory where chunk files are written.

        Returns:
            {
                "status":      "success",
                "video_url":   "...",
                "chunk_paths": ["audio_chunks/chunk_000.mp3", ...]
            }

            OR

            {
                "status":  "error",
                "message": "..."
            }
        """

        os.makedirs(output_dir, exist_ok=True)
        full_audio_path = os.path.join(output_dir, "full_audio.mp3")

        try:

            # ── Step 1: download full audio ────────────────────────────

            current_dir = os.path.dirname(os.path.abspath(__file__))
            cookies_path = os.path.join(current_dir, "youtube_cookies.txt")

            logger.info(f"Downloading audio for: {video_url}")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(output_dir, "full_audio.%(ext)s"),
                "quiet": True,
                "noplaylist": True,
                'cookies_from_browser': 'edge',
                # Emulate a real desktop browser request to minimize 429 risks
                "cookiefile" : cookies_path,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.0.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128"
                    }
                ]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            if not os.path.exists(full_audio_path):
                raise FileNotFoundError(
                    f"Expected full audio at {full_audio_path} but file was not found."
                )

            logger.info("Full audio downloaded successfully.")

            # ── Step 2: split with ffmpeg ──────────────────────────────
            chunk_pattern = os.path.join(output_dir, "chunk_%03d.mp3")

            logger.info(
                f"Splitting audio into {chunk_seconds}s chunks …"
            )

            split_cmd = [
                "ffmpeg",
                "-y",                          # overwrite without asking
                "-i", full_audio_path,
                "-f", "segment",
                "-segment_time", str(chunk_seconds),
                "-c", "copy",                  # no re-encode → fast
                "-reset_timestamps", "1",
                chunk_pattern
            ]

            result = subprocess.run(
                split_cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg split failed:\n{result.stderr}"
                )

            # ── Step 3: collect chunk paths ────────────────────────────
            chunk_paths: List[str] = sorted(
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("chunk_") and f.endswith(".mp3")
            )

            if not chunk_paths:
                raise RuntimeError(
                    "ffmpeg ran without error but produced no chunk files."
                )

            logger.info(
                f"Audio split into {len(chunk_paths)} chunk(s): "
                + ", ".join(os.path.basename(p) for p in chunk_paths)
            )

            # ── Step 4: remove full audio to save disk space ───────────
            os.remove(full_audio_path)
            logger.info("Removed full audio file after chunking.")

            return {
                "status":      "success",
                "video_url":   video_url,
                "chunk_paths": chunk_paths
            }

        except Exception as error:

            logger.error(f"Audio chunking failed: {str(error)}")

            # Clean up partial full-audio file if it exists
            if os.path.exists(full_audio_path):
                try:
                    os.remove(full_audio_path)
                except OSError:
                    pass

            return {
                "status":  "error",
                "message": str(error)
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def cleanup_chunks(self, output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
        """
        Delete all chunk MP3 files from output_dir after processing.
        Call this once TranscriptService has finished with the chunks.
        """

        removed = 0

        for fname in os.listdir(output_dir):
            if fname.startswith("chunk_") and fname.endswith(".mp3"):
                try:
                    os.remove(os.path.join(output_dir, fname))
                    removed += 1
                except OSError as e:
                    logger.warning(f"Could not remove {fname}: {e}")

        logger.info(f"Cleaned up {removed} chunk file(s) from {output_dir}.")


# ==========================================
# Example Usage
# ==========================================

if __name__ == "__main__":

    service = YoutubeService()

    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Metadata only
    info = service.get_video_info(url)
    print("Video info:", info)

    # Download + split into 10-min chunks
    result = service.download_audio_chunks(url, chunk_seconds=600)
    print("Chunk result:", result)

