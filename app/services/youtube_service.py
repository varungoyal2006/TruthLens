import yt_dlp

def download_video(video_url: str, output_path="temp.mp4") -> str:
    ydl_opts = {"outtmpl": output_path}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return output_path