# orchestrates nodes sequentially
# from app.graph.state import TruthLensState
# from app.graph.nodes import video_download_node, transcript_node, claim_extraction_node, search_node, verification_node, report_node

# def run_audit_workflow(video_url: str) -> dict:
#     state: TruthLensState = {
#         "video_url": video_url,
#         "transcript": "",
#         "claims": [],
#         "search_results": {},
#         "verification_results": {},
#         "final_report": {},
#         "error": ""
#     }

#     try:
#         state = transcript_node(state)
#         state = claim_extraction_node(state)
#         state = search_node(state)
#         state = verification_node(state)
#         state = report_node(state)

#     except Exception as e:
#         state['error'] = str(e)

#     return state['final_report']