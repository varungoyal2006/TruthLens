class SearchService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def search_evidence(self, claims: list) -> dict:
        results = {}
        for claim in claims:
            results[claim] = ["https://trusted-source.com"]
        return results