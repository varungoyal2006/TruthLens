import os 
from langgraph.graph import StateGraph, START, END 
from app.graph.state import TruthLensState 
from app.graph.node import youtube_node, transcript_node, claim_extraction_node, search_node, verification_node, report_node 


workflow = StateGraph(TruthLensState)

workflow.add_node("download_audio", youtube_node)
workflow.add_node("extract_transcript", transcript_node)
workflow.add_node("extract_claims", claim_extraction_node)
workflow.add_node("search_evidence", search_node)
workflow.add_node("verify_claims", verification_node)
workflow.add_node("generate_report", report_node)

workflow.add_edge(START, "download_audio")
workflow.add_edge("download_audio", "extract_transcript")
workflow.add_edge("extract_transcript", "extract_claims")
workflow.add_edge("extract_claims", "search_evidence")
workflow.add_edge("search_evidence", "verify_claims")
workflow.add_edge("verify_claims", "generate_report")
workflow.add_edge("generate_report", END)

truth_lens_app = workflow.compile()
if __name__ == "__main__" : 
  initial_input = {
    "video_url": "https://www.youtube.com/shorts/PR50ku-TnY8"
  }

  final_state = truth_lens_app.invoke(initial_input)

  print(final_state["final_report"])