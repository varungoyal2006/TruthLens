class YoutubeService:
    def __init__(self):
        pass  # could add download folder, logging, etc.

    def download_video(self, video_url: str, output_path="temp.mp4") -> str:
        """
        Download video from YouTube or URL.
        Input: video_url (str)
        Output: local file path (str)
        """
        import yt_dlp
        ydl_opts = {"outtmpl": output_path}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return output_path
    

# Input: video_url (string)
# Output: local file path (string, e.g., "temp.mp4")