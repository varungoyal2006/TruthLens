def verify_claims(claims: list, search_results: dict) -> dict:
    results = {}
    for claim in claims:
        results[claim] = {
            "verdict": "False",
            "confidence": 90,
            "sources": search_results.get(claim, [])
        }
    return results