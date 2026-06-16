```python
"""
Shared workflow state for TruthLens.

Each node updates this state and passes it
to the next node in the workflow.
"""

from typing import TypedDict, List, Dict


class TruthLensState(TypedDict):

    # Input YouTube URL
    video_url: str

    # Downloaded audio path
    audio_path: str

    # Extracted transcript
    transcript: str

    # Claims extracted from transcript
    claims: List[str]

    # Tavily search results
    search_results: Dict

    # Verification results
    verification_results: Dict

    # Final generated report
    final_report: Dict

    # Error tracking
    error: str
```
