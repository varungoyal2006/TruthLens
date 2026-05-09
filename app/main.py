# # Purpose: Entry point of FastAPI backend. Connects all routes and starts the server.

# from fastapi import FastAPI
# from app.api.audit_routes import router as audit_router

# app = FastAPI(title="TruthLens API")

# # Include API routes
# app.include_router(audit_router, prefix="/audit")

# @app.get("/")
# def root():
#     return {"message": "TruthLens API Running!"}
