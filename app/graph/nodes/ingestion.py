import logging
from app.graph.state import TruthLensState
from app.services.youtube import YoutubeService 
from app.services.transcript import TransScriptService

logger = logging.getLogger(__name__)

def ingestion_node(state: TruthLensState) -> dict: 
    logger.info("Ingestion node processing phase started.")
    try: 
        youtube = YoutubeService() 
        transcript = TransScriptService() 

        video_url = state.get("video_url")
        if not video_url:
            raise ValueError("No video_url found in the state context.")

        yt_result = youtube.download_audio_chunks(video_url=video_url)
        if yt_result.get("status") != "success": 
            raise RuntimeError(f"YoutubeService failed: {yt_result.get('message', 'Unknown Error')}")

        logger.info(f"Successfully staged {len(yt_result['chunk_paths'])} audio chunks for transcription.")

        ts_result = transcript.extract_transcript_from_chunks(chunk_paths=yt_result["chunk_paths"])
        if ts_result.get("status") != "success": 
            raise RuntimeError(f"TranscriptService failed: {ts_result.get('message', 'Unknown Error')}")

        logger.info("Full transcript extraction completed successfully.")

        # CRITICAL FIX: Return ONLY the new keys as a dictionary delta

        print(ts_result["transcript"])
        
        return {
            "chunk_paths": yt_result["chunk_paths"],
            "transcript": ts_result["transcript"]
        }

    except Exception as node_error: 
        error_msg = f"Fatal system interruption in ingestion node: {str(node_error)}"
        logger.error(error_msg)
        return {"error": error_msg}