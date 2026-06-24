"""
Transcript Service Module

Converts audio files (or a list of audio chunks) into a single merged
transcript using Groq's Whisper model.

Workflow (single file):
    audio.mp3  →  Groq Whisper  →  transcript (str)

Workflow (chunked long video):
    [chunk_000.mp3, chunk_001.mp3, ...]
              ↓  (parallel Groq Whisper calls)
    ["chunk 0 text ...", "chunk 1 text ...", ...]
              ↓  (merge in order)
    full merged transcript (str)
"""

import os
import logging
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Groq Whisper hard limit — stay safely below it
GROQ_MAX_BYTES = 24 * 1024 * 1024   # 24 MB


class TranscriptService:
    """
    Service class for transcript extraction using Groq Whisper.

    Supports both single-file and multi-chunk (long video) workflows.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize Groq client.

        Args:
            api_key (str, optional):
                Groq API key. Defaults to GROQ_API_KEY env variable.
        """

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Please add it to your .env file."
            )

        self.client = Groq(api_key=self.api_key)

    # ------------------------------------------------------------------
    # Public: single file  (original behaviour, unchanged)
    # ------------------------------------------------------------------

    def extract_transcript(
        self,
        video_path: str
    ) -> Dict[str, str]:
        """
        Extract transcript from a single audio/video file.

        Args:
            video_path (str): Local path to the audio/video file.

        Returns:
            {
                "status":     "success",
                "video_path": "...",
                "transcript": "..."
            }

            OR

            {
                "status":  "error",
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

            file_size = os.path.getsize(video_path)
            if file_size > GROQ_MAX_BYTES:
                raise ValueError(
                    f"File is {file_size / 1e6:.1f} MB which exceeds Groq's "
                    f"25 MB limit. Use extract_transcript_from_chunks() instead."
                )

            with open(video_path, "rb") as media_file:

                transcription = (
                    self.client.audio.transcriptions.create(
                        file=media_file,
                        model="whisper-large-v3"
                    )
                )

            logger.info("Transcript extraction completed successfully.")

            return {
                "status":     "success",
                "video_path": video_path,
                "transcript": transcription.text
            }

        except Exception as error:

            logger.error(
                f"Transcript extraction failed: {str(error)}"
            )

            return {
                "status":  "error",
                "message": str(error)
            }

    # ------------------------------------------------------------------
    # Public: multi-chunk  ← NEW
    # ------------------------------------------------------------------

    def extract_transcript_from_chunks(
        self,
        chunk_paths: List[str],
        max_workers: int = 3
    ) -> Dict[str, str]:
        """
        Transcribe a list of audio chunk files in parallel, then merge
        them in order into a single transcript string.

        This is the correct entry-point for long videos that were split
        by YoutubeService.download_audio_chunks().

        Args:
            chunk_paths (List[str]):
                Ordered list of chunk file paths, e.g.
                ["audio_chunks/chunk_000.mp3", "audio_chunks/chunk_001.mp3"]

            max_workers (int):
                Max parallel Groq Whisper calls (default 3).
                Keep low to avoid Groq rate-limit errors.

        Returns:
            {
                "status":       "success",
                "total_chunks": 4,
                "transcript":   "merged full transcript ..."
            }

            OR

            {
                "status":  "error",
                "message": "..."
            }
        """

        if not chunk_paths:
            return {
                "status":  "error",
                "message": "No chunk paths provided."
            }

        logger.info(
            f"Starting chunked transcript extraction "
            f"({len(chunk_paths)} chunk(s), {max_workers} workers) …"
        )

        # results[i] will hold the transcript text for chunk i
        results: Dict[int, str] = {}
        errors:  List[str]      = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            future_to_index = {
                executor.submit(self._transcribe_single_chunk, path, idx): idx
                for idx, path in enumerate(chunk_paths)
            }

            for future in as_completed(future_to_index):

                idx = future_to_index[future]

                try:
                    text = future.result()
                    results[idx] = text
                    logger.info(
                        f"Chunk {idx} transcribed "
                        f"({len(text)} chars)."
                    )

                except Exception as e:
                    error_msg = f"Chunk {idx} failed: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    results[idx] = ""   # keep ordering; empty string for failed chunk

        if errors:
            # Log but don't abort — partial transcript is better than nothing
            logger.warning(
                f"{len(errors)} chunk(s) failed. "
                "Merging available transcripts."
            )

        # Merge in original order with a blank line between chunks
        # so claim extraction sees clean sentence boundaries
        merged_transcript = "\n\n".join(
            results[i]
            for i in sorted(results.keys())
            if results[i].strip()
        )

        if not merged_transcript.strip():
            return {
                "status":  "error",
                "message": "All chunks failed to transcribe."
            }

        logger.info(
            f"Merged transcript ready: {len(merged_transcript)} chars "
            f"from {len(results)} chunk(s)."
        )

        return {
            "status":        "success",
            "total_chunks":  len(chunk_paths),
            "failed_chunks": len(errors),
            "transcript":    merged_transcript
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _transcribe_single_chunk(
        self,
        chunk_path: str,
        chunk_index: int
    ) -> str:
        """
        Transcribe one audio chunk and return its text.

        Raises on error so the ThreadPoolExecutor can catch it.
        """

        if not os.path.exists(chunk_path):
            raise FileNotFoundError(
                f"Chunk file not found: {chunk_path}"
            )

        file_size = os.path.getsize(chunk_path)
        if file_size > GROQ_MAX_BYTES:
            raise ValueError(
                f"Chunk {chunk_index} is {file_size / 1e6:.1f} MB — "
                f"exceeds Groq's 25 MB limit. Reduce chunk_seconds."
            )

        logger.info(
            f"Transcribing chunk {chunk_index}: {chunk_path} "
            f"({file_size / 1e6:.1f} MB)"
        )

        with open(chunk_path, "rb") as f:
            transcription = self.client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3"
            )

        return transcription.text


# ==========================================
# Example Usage
# ==========================================

if __name__ == "__main__":

    service = TranscriptService()

    # Single file
    result = service.extract_transcript("temp.mp4")
    print("Single:", result)

    # Multiple chunks (after YoutubeService.download_audio_chunks)
    chunks = [
        "audio_chunks/chunk_000.mp3",
        "audio_chunks/chunk_001.mp3",
        "audio_chunks/chunk_002.mp3",
    ]
    result = service.extract_transcript_from_chunks(chunks)
    print("Chunked:", result["transcript"][:200])
