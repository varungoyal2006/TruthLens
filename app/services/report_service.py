# class ReportService:
#     def __init__(self):
#         pass

#     def generate_report(self, verification_results: dict) -> dict:
#         """
#         Input: verification_results (dict from VerificationService)
#         Output: structured final report (dict)
#         Example:
#         {
#             "overall_score": 50,
#             "summary": "Video contains misleading claims",
#             "results": {
#                 "5G causes cancer": {"verdict": "False", "confidence": 92, "sources": ["https://trusted-source.com"]},
#                 "NASA confirmed aliens": {"verdict": "False", "confidence": 80, "sources": ["https://trusted-source.com"]}
#             }
#         }
#         """
#         return {
#             "overall_score": 50,
#             "summary": "MVP report summary",
#             "results": verification_results
#         }

# Input: verification_results (dict)
# Output: final_report (dict)