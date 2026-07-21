"""
API REQUEST SCHEMAS
"""

from pydantic import BaseModel, HttpUrl, Field 

class AuditRequest(BaseModel): 
  video_url : HttpUrl = Field(
    ..., 
    description="The full URL of the Youtube video or short to anaylze."
  )