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

import logging

# Set up logging
logger = logging.getLogger(__name__)

class ReportService:
    """
    Service to compile individual verification results into a structured, 
    easily readable final report with an aggregated score and summary.
    """
    def __init__(self):
        # Initialization logic can be added here if needed in the future
        pass

    def generate_report(self, verification_results: dict) -> dict:
        """
        Input: verification_results (dict from VerificationService)
        Output: structured final report (dict)
        
        Example Input:
        {
            "5G causes cancer": {"verdict": "False", "confidence": 92, "sources": ["https://trusted-source.com"]},
            "NASA confirmed aliens": {"verdict": "False", "confidence": 80, "sources": ["https://trusted-source.com"]}
        }
        """
        logger.info(f"Generating report for {len(verification_results)} verified claims.")

        # Handle empty input gracefully
        if not verification_results:
            return {
                "overall_score": 0,
                "summary": "No claims were provided for verification.",
                "results": {}
            }

        # 1. Calculate an aggregated "Trust Score"
        total_score = 0
        for claim, data in verification_results.items():
            verdict = data.get("verdict", "").lower()
            
            # Assign point values based on common fact-checking verdicts
            if verdict == "true":
                total_score += 100
            elif verdict in ["mostly true", "partially true"]:
                total_score += 75
            elif verdict == "misleading":
                total_score += 50
            elif verdict == "false":
                total_score += 0
            else:
                # Default middle ground for unknown or unverifiable claims
                total_score += 50 

        # Calculate the average score
        overall_score = round(total_score / len(verification_results))

        # 2. Generate a dynamic summary based on the score
        if overall_score >= 80:
            summary = "The content is mostly factual and well-supported."
        elif overall_score >= 50:
            summary = "The content contains a mix of factual and misleading claims."
        else:
            summary = "The content is largely false and contains highly misleading claims."

        # 3. Compile and return the final report
        final_report = {
            "overall_score": overall_score,
            "summary": summary,
            "results": verification_results
        }

        return final_report

# ==========================================
# Example Usage:
# ==========================================
if __name__ == "__main__":
    # Mock data from a previous VerificationService step
    mock_results = {
        "5G causes cancer": {
            "verdict": "False", 
            "confidence": 92, 
            "sources": ["https://who.int/5g-facts"]
        },
        "Water boils at 100C": {
            "verdict": "True", 
            "confidence": 99, 
            "sources": ["https://science-facts.com"]
        }
    }

    service = ReportService()
    report = service.generate_report(mock_results)
    
    import json
    print(json.dumps(report, indent=4))