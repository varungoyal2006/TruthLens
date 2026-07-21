"""
Audit Workflow Router
Exposes the LangGraph state machine execution engine to web clients.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.requests import AuditRequest
from app.schemas.responses import AuditResponse
from app.graph.workflow import truth_lens_app

logger = logging.getLogger(__name__)
router = APIRouter()

# Note: We use standard `def` instead of `async def` because the underlying 
# services currently use synchronous HTTP clients. FastAPI will automatically 
# run this in a background worker thread to prevent server blocking.
@router.post("/analyze", summary="Analyze a Video URL", response_model=AuditResponse)
def analyze_video(request: AuditRequest):
    logger.info(f"Received API request to analyze URL: {request.video_url}")
    
    try:
        initial_input = {"video_url": str(request.video_url)}
        
        # Trigger the LangGraph execution pipeline
        final_state = truth_lens_app.invoke(initial_input)
        
        # Check if the graph short-circuited due to an error
        if final_state.get("error"):
            logger.error(f"Workflow failed during execution: {final_state['error']}")
            raise HTTPException(
                status_code=500, 
                detail=final_state["error"]
            )
            
        # Return the final compiled report
        return final_state.get("final_report", {})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled API error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )