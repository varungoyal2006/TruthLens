# define all nodes (functions) in workflow
# from app.graph.state import TruthLensState
# from app.services.youtube_service import download_video
# from app.services.transcript_service import extract_transcript
# from app.services.claim_service import extract_claims
# from app.services.search_service import search_evidence
# from app.services.verification_service import verify_claims
# from app.services.report_service import generate_report

# def transcript_node(state: TruthLensState):
#     state['transcript'] = extract_transcript(state['video_url'])
#     return state

# def claim_extraction_node(state: TruthLensState):
#     state['claims'] = extract_claims(state['transcript'])
#     return state

# def search_node(state: TruthLensState):
#     state['search_results'] = search_evidence(state['claims'])
#     return state

# def verification_node(state: TruthLensState):
#     state['verification_results'] = verify_claims(state['claims'], state['search_results'])
#     return state

# def report_node(state: TruthLensState):
#     state['final_report'] = generate_report(state['verification_results'])
#     return state