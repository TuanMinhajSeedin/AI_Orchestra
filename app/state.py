from typing import List, Optional

from pydantic import BaseModel, Field


class ResearchState(BaseModel):
    """
    Shared orchestration state flowing through the LangGraph graph.

    This model is designed to be passed between nodes and mutated as the
    research pipeline progresses.
    """

    # STEP 2 required fields
    user_query: str

    # Planner output (STEP 3)
    research_topics: List[str] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    analysis_steps: List[str] = Field(default_factory=list)

    # Downstream pipeline fields
    # List of dictionaries from WebSearchAgent:
    # { "title": str, "source": str, "content": str, "url": str }
    search_results: List[dict] = Field(default_factory=list)
    # List of dictionaries from AnalyzerAgent:
    # { "finding": str, "evidence": str, "source": str }
    extracted_insights: List[dict] = Field(default_factory=list)

    # Orchestration bookkeeping
    # Used to implement simple retry logic for the search step.
    search_attempts: int = 0
    summary: str = ""
    final_report: str = ""
    status: str = Field(
        default="pending",
        description="Overall orchestration status, e.g. pending|running|completed|error",
    )
    error: Optional[str] = None

