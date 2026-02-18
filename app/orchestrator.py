from typing import Any, Dict
import logging

from langgraph.graph import END, StateGraph

from app.state import ResearchState
from app.agents.planner import PlannerAgent
from app.agents.search_agent import WebSearchAgent
from app.agents.analyzer import AnalyzerAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.tools.web_search import WebSearchTool
from app.tools.url_loader import UrlLoader
from app.tools.vector_store import VectorStore
from app.llm import LLM


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    LangGraph-based orchestrator wiring together the research agents.

    The current implementation is intentionally minimal and mostly
    deterministic. Replace internal logic with LLM calls as needed.
    """

    def __init__(self) -> None:
        # Initialize tools
        web_search = WebSearchTool()
        vector_store = VectorStore()
        url_loader = UrlLoader()

        # Initialize shared LLM
        llm = LLM()

        # Initialize agents
        planner = PlannerAgent(llm=llm)
        searcher = WebSearchAgent(web_search=web_search, vector_store=vector_store, url_loader=url_loader)
        analyzer = AnalyzerAgent(llm=llm)
        summarizer = SummarizerAgent(llm=llm)
        reporter = ReportGeneratorAgent(llm=llm)

        # Build LangGraph
        graph = StateGraph(ResearchState)

        # Register nodes
        graph.add_node("planner", planner)
        graph.add_node("search", searcher)
        graph.add_node("analyzer", analyzer)
        graph.add_node("summarizer", summarizer)
        graph.add_node("reporter", reporter)

        # Orchestration flow with conditional handling
        # START -> planner
        graph.set_entry_point("planner")
        # Planner always proceeds to search
        graph.add_edge("planner", "search")

        # After search:
        # - If search_results is empty and we have attempted fewer than 2 times,
        #   go back to search (retry).
        # - Otherwise, proceed to analyzer.
        def route_after_search(state: ResearchState) -> str:
            if not state.search_results and state.search_attempts < 2:
                return "retry_search"
            return "to_analyzer"

        graph.add_conditional_edges(
            "search",
            route_after_search,
            {
                "retry_search": "search",
                "to_analyzer": "analyzer",
            },
        )

        # After analyzer:
        # - If extracted_insights is empty, mark error state and end.
        # - Otherwise, continue to summarizer.
        def route_after_analyzer(state: ResearchState) -> str:
            if not state.extracted_insights:
                return "error_end"
            return "to_summarizer"

        graph.add_conditional_edges(
            "analyzer",
            route_after_analyzer,
            {
                "to_summarizer": "summarizer",
                "error_end": END,
            },
        )

        # Linear flow for final steps
        graph.add_edge("summarizer", "reporter")
        graph.add_edge("reporter", END)

        self.app = graph.compile()
        logger.info("Orchestrator: LangGraph compiled with nodes: planner -> search -> analyzer -> summarizer -> reporter.")

    async def run_state(self, query: str) -> ResearchState:
        """
        Execute the research graph for a given query and return the final state.

        This is useful for inspecting status, errors, and intermediate fields.
        """
        logger.info("Orchestrator: Starting run_state for query: %r", query)
        initial_state = ResearchState(user_query=query)
        final_state: Any = await self.app.ainvoke(initial_state)

        # LangGraph may return a dict-like object instead of the Pydantic model.
        if isinstance(final_state, ResearchState):
            state = final_state
        elif isinstance(final_state, dict):
            state = ResearchState(**final_state)
        else:
            # Fallback: attempt to coerce to dict, then to ResearchState
            try:
                state = ResearchState(**dict(final_state))  # type: ignore[arg-type]
            except Exception:
                state = initial_state
                state.status = "error"
                state.error = "Failed to decode final orchestration state."
                logger.info("Orchestrator: Failed to decode final state; returning error state.")
                return state

        # Mark completion if no error has been set.
        if state.status != "error":
            state.status = "completed"
            logger.info("Orchestrator: Completed run_state successfully.")
        else:
            logger.info("Orchestrator: Finished with error status: %s (%s)", state.status, state.error)
        return state

    async def run(self, query: str) -> str:
        """
        Convenience wrapper: run orchestration and return only the final report.
        """
        state = await self.run_state(query)
        return state.final_report or ""


