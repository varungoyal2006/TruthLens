```python
"""
Workflow Nodes

Each node performs one step of the TruthLens
fact-checking pipeline and updates the shared state.
"""

from app.graph.state import TruthLensState

from app.services.youtube_service import YoutubeService
from app.services.transcript_service import TranscriptService
from app.services.claim_service import ClaimService
from app.services.search_service import SearchService
from app.services.verification_service import VerificationService
from app.services.report_service import ReportService


youtube_service = YoutubeService()
transcript_service = TranscriptService()
claim_service = ClaimService()
search_service = SearchService()
verification_service = VerificationService()
report_service = ReportService()


def youtube_node(
    state: TruthLensState
) -> TruthLensState:

    try:

        result = youtube_service.download_audio(
            state["video_url"]
        )

        if result["status"] == "error":
            state["error"] = result["message"]
            return state

        state["audio_path"] = result["audio_path"]

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def transcript_node(
    state: TruthLensState
) -> TruthLensState:

    try:

        result = transcript_service.extract_transcript(
            state["audio_path"]
        )

        if result["status"] == "error":
            state["error"] = result["message"]
            return state

        state["transcript"] = result["transcript"]

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def claim_extraction_node(
    state: TruthLensState
) -> TruthLensState:

    try:

        claims = claim_service.extract_claims(
            state["transcript"]
        )

        state["claims"] = claims

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def search_node(
    state: TruthLensState
) -> TruthLensState:

    try:

        results = search_service.search_evidence(
            state["claims"]
        )

        state["search_results"] = results

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def verification_node(
    state: TruthLensState
) -> TruthLensState:

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

            result = (
                verification_service.verify_claim(
                    claim,
                    evidence_text
                )
            )

            verification_results[claim] = result

        state["verification_results"] = (
            verification_results
        )

        return state

    except Exception as error:

        state["error"] = str(error)
        return state


def report_node(
    state: TruthLensState
) -> TruthLensState:

    try:

        report = (
            report_service.generate_report(
                state["verification_results"]
            )
        )

        state["final_report"] = report

        return state

    except Exception as error:

        state["error"] = str(error)
        return state
```
