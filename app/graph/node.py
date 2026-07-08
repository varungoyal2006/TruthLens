"""
Workflow Nodes

Each node performs one step of the TruthLens fact-checking pipeline
and updates the shared state.

Chunked video flow (long videos):
    youtube_node  →  downloads audio + splits into chunks
    transcript_node  →  transcribes each chunk, merges into one transcript
    claim_extraction_node  →  extracts claims from merged transcript
    search_node  →  searches evidence for each claim (parallel)
    verification_node  →  verifies each claim against evidence
    report_node  →  compiles final trust-score report
"""

from app.graph.state import TruthLensState

from app.services.youtube_service     import YoutubeService
from app.services.transcript  import TranscriptService
from app.services.claim       import ClaimService
from app.services.search      import SearchService
from app.services.verification import VerificationService
from app.services.report_service      import ReportService


youtube_service      = YoutubeService()
transcript_service   = TranscriptService()
claim_service        = ClaimService()
search_service       = SearchService()
verification_service = VerificationService()
report_service       = ReportService()


def youtube_node(state: TruthLensState) -> TruthLensState:
    """
    Downloads YouTube audio and splits it into chunks.

    Stores chunk_paths in state for the transcript node.
    Falls back to a single-file download if chunking fails unexpectedly.
    """

    try:

        result = youtube_service.download_audio_chunks(
            state["video_url"],
            chunk_seconds=600   # 10-minute chunks
        )

        if result["status"] == "error":
            state["error"] = result["message"]
            return state

        # Store list of chunk paths instead of a single audio path
        state["chunk_paths"] = result["chunk_paths"]

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def transcript_node(state: TruthLensState) -> TruthLensState:
    """
    Transcribes all audio chunks in parallel and merges them into
    a single transcript string.
    """

    try:

        chunk_paths = state.get("chunk_paths", [])

        if not chunk_paths:
            state["error"] = "No audio chunks found to transcribe."
            return state

        result = transcript_service.extract_transcript_from_chunks(
            chunk_paths
        )

        if result["status"] == "error":
            state["error"] = result["message"]
            return state

        state["transcript"] = result["transcript"]

        # Clean up chunk files from disk once we have the transcript
        youtube_service.cleanup_chunks()

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def claim_extraction_node(state: TruthLensState) -> TruthLensState:
    """
    Extracts factual, verifiable claims from the merged transcript.
    Claims are extracted once from the full transcript.
    """

    try:

        claims = claim_service.extract_claims(
            state["transcript"]
        )

        state["claims"] = claims

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def search_node(state: TruthLensState) -> TruthLensState:
    """
    Searches for evidence for each claim using Tavily (parallel).
    """

    try:

        results = search_service.search_evidence(
            state["claims"]
        )

        state["search_results"] = results

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def verification_node(state: TruthLensState) -> TruthLensState:
    """
    Verifies each claim against its retrieved evidence using Groq LLaMA 3.
    """

    try:

        verification_results = {}

        for claim in state["claims"]:

            evidence_list = (
                state["search_results"]
                .get(claim, [])
            )

            evidence_text = "\n".join(
                item.get("snippet", "")
                for item in evidence_list
            )

            result = verification_service.verify_claim(
                claim,
                evidence_text
            )

            verification_results[claim] = result

        state["verification_results"] = verification_results

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def report_node(state: TruthLensState) -> TruthLensState:
    """
    Compiles all verification results into a final trust-score report.
    """

    try:

        report = report_service.generate_report(
            state["verification_results"]
        )

        state["final_report"] = report

        return state

    except Exception as error:

        state["error"] = str(error)
        return state
