""""
HEALT CHECK ROUTER 
USED BY DEPLOYMENT PLATFORMS (DOCKERE/AWS) TO VERIFY SERVER UPTIEM 
"""
from fastapi import APIRouter 

router = APIRouter() 

@router.get("/health", summary="Perform a Health Check")
def health_check(): 
  return {"status" : "online", "message" : "TruthLens API is opeartional"}

