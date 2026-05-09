class TranscriptService:
    def __init__(self, api_key: str = None):
        # Optional: store API key or client instance
        self.api_key = api_key

    def extract_transcript(self, video_url: str) -> str:
        # Replace this with actual Whisper / AWS Transcribe logic
        transcript = "Dummy transcript for MVP"
        return transcript