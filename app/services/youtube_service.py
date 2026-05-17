import yt_dlp
#improves readability , helps understand function return types clearly dict[str,str].
from typing import Dict

class YoutubeService:

    def download_video(self,video_url: str,output_path: str = "temp.mp4") -> Dict[str, str]:


        try:
            #This stores yt_dlp configuration.
            ydl_opts = {
                #Defines output filename/template.
                "outtmpl": output_path, 
                # Suppresses unnecessary logs during download
                "quiet": True
            }
            #yt_dlp.YoutubeDL() -> creates a downloader object using the provided settings.
            # with safely manages the downloader resource & automatically handles cleanup
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            return {
                "status": "success",
                "video_url": video_url,
                "video_path": output_path
            }

        except Exception as error:

            return {
                "status": "error",
                "message": str(error)
            }