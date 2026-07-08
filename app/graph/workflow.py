"""
TruthLens LangGraph Workflow Module

Compiles the state machine graph, linking ingestion, extraction, 
retrieval, and verification nodes. Includes conditional routing 
to handle pipeline errors gracefully and prevent cascade failures.
"""

import logging
import json
import sys

from app.core.logger import setup_logging

from langgraph.graph import StateGraph, START, END 

from app.graph.state import TruthLensState 
from app.graph.nodes.ingestion import ingestion_node
from app.graph.nodes.extraction import extraction_node
from app.graph.nodes.retrieval import retrieval_node
from app.graph.nodes.verification import verification_node

# Initialize logger using standard module-level resolution
logger = logging.getLogger(__name__)

# ==========================================
# Routing Logic
# ==========================================

def route_on_error(state: TruthLensState) -> str:
    """
    Evaluates the state after a node finishes. 
    If an error was caught and logged into state['error'], it short-circuits 
    the graph directly to the END node.
    """
    if state.get("error"):
        logger.warning(f"Graph Router detected an error state. Short-circuiting to END.")
        return "error_detected"
    return "continue"

# ==========================================
# Graph Construction
# ==========================================

logger.info("Initializing TruthLens StateGraph...")
workflow = StateGraph(TruthLensState)

# 1. Register Nodes
workflow.add_node("ingestion", ingestion_node)
workflow.add_node("extraction", extraction_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("verification", verification_node)

# 2. Define Execution Edges with Fault Tolerance
workflow.add_edge(START, "ingestion")

# Post-Ingestion Branch
workflow.add_conditional_edges(
    "ingestion", 
    route_on_error, 
    {
        "continue": "extraction", 
        "error_detected": END
    }
)

# Post-Extraction Branch
workflow.add_conditional_edges(
    "extraction", 
    route_on_error, 
    {
        "continue": "retrieval", 
        "error_detected": END
    }
)

# Post-Retrieval Branch
workflow.add_conditional_edges(
    "retrieval", 
    route_on_error, 
    {
        "continue": "verification", 
        "error_detected": END
    }
)

# Verification is the final operational node
workflow.add_edge("verification", END) # Fixed bug: Uses END constant, not "END" string

# ==========================================
# Graph Compilation
# ==========================================

truth_lens_app = workflow.compile()
logger.info("TruthLens LangGraph compiled successfully.")

# ==========================================
# Developer Testing Block
# ==========================================
if __name__ == "__main__": 
    setup_logging()

    initial_input = {
        "video_url": "https://www.youtube.com/watch?v=2BYoinvcFxo"
    }

    try:
        print("\n🚀 Invoking TruthLens Workflow...\n")
        final_state = truth_lens_app.invoke(initial_input)

        if final_state.get("error"):
            print("\n❌ Workflow terminated with an error:")
            print(final_state["error"])
        else:
            print("\n✅ Workflow Completed Successfully!")
            print("\n--- Final TruthLens Report ---")
            print(json.dumps(final_state.get("final_report"), indent=4))
            
    except Exception as e:
        print(f"\n❌ Uncaught Execution Exception: {e}")