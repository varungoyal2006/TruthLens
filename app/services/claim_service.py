# class ClaimService:
#     def __init__(self, llm_client=None):
#         self.llm_client = llm_client  # GPT-4o, for example

#     def extract_claims(self, transcript: str) -> list:
#         """
#         Input: transcript text (str)
#         Output: list of claim strings (list[str])
#         """
#         # Example MVP output
#         return ["5G causes cancer", "NASA confirmed aliens"]

# Input: transcript (string)
# Output: claims (list of strings)

# Later: You can return structured claims with timestamps using a Claim model:

# [
#     {"text": "5G causes cancer", "timestamp": "00:31"},
#     {"text": "NASA confirmed aliens", "timestamp": "01:12"}
# ]