# Purpose: FastAPI endpoints (routes). Handles HTTP requests.


# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.graph.workflow import run_audit_workflow

# router = APIRouter()

# # Request model
# class AuditRequest(BaseModel):
#     video_url: str

# # Response model
# class AuditResponse(BaseModel):
#     status: str
#     report: dict

@app.get("/hi")
# def get_report():
#     return {"message": "TruthLens API Running!"}
def get_report(): 
  