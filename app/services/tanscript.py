import os
import sys
import logging
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from groq import Groq
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Logger for this module
logger = logging.getLogger(__file__)

# Maximum audio size accepted by Groq Whisper (24 MB)
GROQ_MAX_BYTES = 24 * 1024 * 1024


class TransScriptService:
    """
    Handles audio transcription using Groq Whisper.

    Supports:
    - Transcribing a single audio file.
    - Transcribing multiple audio chunks concurrently.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the Groq client.
        """

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set.")

        self.client = Groq(api_key=self.api_key)

    def extract_transcript(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe a single audio file.

        Returns:
            {
                status,
                video_path,
                transcript
            }
        """

        try:
            logger.info(f"Starting transcription: {audio_path}")

            if not os.path.exists(audio_path):
                raise FileNotFoundError("Audio file not found.")

            file_size = os.path.getsize(audio_path)

            if file_size > GROQ_MAX_BYTES:
                raise ValueError("Audio file exceeds Groq's maximum upload size.")

            with open(audio_path, "rb") as media_file:
                transcription = self.client.audio.transcriptions.create(
                    file=media_file,
                    model="whisper-large-v3",
                )

            logger.info("Transcription completed successfully.")

            return {
                "status": "success",
                "video_path": audio_path,
                "transcript": transcription.text,
            }

        except Exception as error:
            logger.error(f"Transcription failed: {error}")

    def extract_transcript_from_chunks(
        self,
        chunk_path: List[str],
        max_worker: int = 3,
    ) -> Dict[str, Any]:
        """
        Transcribe multiple audio chunks concurrently and merge them.

        Args:
            chunk_path:
                List of chunk file paths.

            max_worker:
                Maximum number of concurrent transcription threads.

        Returns:
            Combined transcript in the correct order.
        """

        if not chunk_path:
            return {
                "status": "error",
                "message": "No chunk paths provided.",
            }

        logger.info("Chunk transcription started.")

        # Stores transcripts keyed by their original chunk index.
        results: Dict[int, str] = {}

        # Stores chunks that failed.
        errors: List[str] = []

        with ThreadPoolExecutor(max_workers=max_worker) as executor:

            # Map every Future object to its original chunk index.
            future_to_index = {
                executor.submit(
                    self._single_extract_transcript,
                    path,
                    idx,
                ): idx
                for idx, path in enumerate(chunk_path)
            }

            # Process completed transcriptions.
            for future in as_completed(future_to_index):

                idx = future_to_index[future]

                try:
                    text = future.result()

                    results[idx] = text

                    logger.info(f"Chunk {idx} transcribed successfully.")

                except Exception as error:
                    logger.error(f"Chunk {idx} failed: {error}")
                    errors.append(str(error))

        # Merge transcripts while preserving the original chunk order.
        merged_transcript = "\n\n".join(
            results[i]
            for i in sorted(results.keys())
            if results[i].strip()
        )

        if not merged_transcript:
            return {
                "status": "error",
                "message": "All chunks failed to transcribe.",
            }

        logger.info("Merged transcript created successfully.")

        return {
            "status": "success",
            "total_chunks": len(chunk_path),
            "failed_chunks": len(errors),
            "transcript": merged_transcript,
        }

    def _single_extract_transcript(
        self,
        audio_path: str,
        audio_index: int,
    ) -> str:
        """
        Worker function used by each thread.

        Transcribes a single audio chunk.
        """

        logger.info(f"Processing chunk {audio_index}: {audio_path}")

        if not os.path.exists(audio_path):
            raise FileNotFoundError("Audio chunk not found.")

        file_size = os.path.getsize(audio_path)

        if file_size > GROQ_MAX_BYTES:
            raise ValueError("Chunk exceeds Groq upload limit.")

        with open(audio_path, "rb") as media_file:
            transcription = self.client.audio.transcriptions.create(
                file=media_file,
                model="whisper-large-v3",
            )

        logger.info(f"Finished chunk {audio_index}")

        return transcription.text


def setup_logging():
    """
    Configure the application's logging.
    """

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


if __name__ == "__main__":
    setup_logging()

    print("Hello World")

    ts = TransScriptService()

    PROJECT_ROOT = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
    )

    AUDIO_OUTPUT_DIR = os.path.join(
        PROJECT_ROOT,
        "tmp",
        "audio_chunks",
    )

    test_chunks = [
        os.path.join(AUDIO_OUTPUT_DIR, "chunk_000.mp3"),
        os.path.join(AUDIO_OUTPUT_DIR, "chunk_001.mp3"),
    ]

    result = ts.extract_transcript_from_chunks(test_chunks)

    print(result)

    print("Hello World")