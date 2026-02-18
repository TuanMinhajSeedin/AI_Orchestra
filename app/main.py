from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from app.orchestrator import Orchestrator


logger = logging.getLogger(__name__)

app = FastAPI(title="AI Research Orchestrator", version="0.1.0")
orchestrator = Orchestrator()


class ResearchRequest(BaseModel):
    query: str


@app.get("/health")
async def health_check() -> dict:
    """Simple health-check endpoint."""
    return {"status": "ok"}


@app.post("/research")
async def run_research(request: ResearchRequest) -> dict:
    """
    Execute the research orchestration pipeline for a given query.

    Process:
    - Initialize shared state
    - Run LangGraph orchestration
    - Return the final markdown report and status
    """
    logger.info("FastAPI: Received /research request for query: %r", request.query)
    state = await orchestrator.run_state(query=request.query)

    if state.status == "error":
        logger.info("FastAPI: Orchestration failed for query: %r (%s)", request.query, state.error)
        # Surface orchestration errors via HTTPException.
        raise HTTPException(
            status_code=500,
            detail={
                "message": state.error or "Orchestration failed",
                "status": state.status,
            },
        )

    logger.info("FastAPI: Orchestration completed for query: %r", request.query)
    return {
        "query": request.query,
        "status": state.status,
        "final_report": state.final_report,
    }


