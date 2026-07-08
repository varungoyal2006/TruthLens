"""
Shared Workflow State for TruthLens.

This module defines the State TypedDict used to track information processing
across the LangGraph pipeline nodes. Reducers are explicitly defined to prevent
LangGraph from silently dropping state updates between nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated

def overwrite_state(existing, new):
    """
    Custom LangGraph reducer. 
    Forces the state machine to aggressively overwrite the existing state key 
    with whatever dictionary value the previous node just returned.
    """
    return new

class TruthLensState(TypedDict):
    """
    The unified state object passed between execution nodes in the LangGraph workflow.
    """

    # ─── INPUT LAYER ──────────────────────────────────────────────────
    video_url: str
    
    # ─── INGESTION LAYER ──────────────────────────────────────────────
    # Annotated with overwrite_state to guarantee the array updates
    chunk_paths: Annotated[List[str], overwrite_state]
    
    transcript: Annotated[str, overwrite_state]

    # ─── EXTRACTION LAYER ─────────────────────────────────────────────
    claims: Annotated[List[Dict[str, str]], overwrite_state]

    # ─── RETRIEVAL & RETROSPECT LAYER ─────────────────────────────────
    evidence_data: Annotated[Dict[str, List[Dict[str, str]]], overwrite_state]
    
    evidence_sources: Annotated[Dict[str, str], overwrite_state]

    # ─── EVALUATION & COMPILATION LAYER ───────────────────────────────
    final_report: Annotated[Dict[str, Any], overwrite_state]

    # ─── FAULT TOLERANCE TRACKING ─────────────────────────────────────
    error: Annotated[Optional[str], overwrite_state]