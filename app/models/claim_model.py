from pydantic import BaseModel

class Claim(BaseModel):
    text: str
    timestamp: str = None