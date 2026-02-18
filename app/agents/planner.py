from typing import List, Dict, Any
import json
import logging

from app.state import ResearchState
from app.llm import LLM


logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Boilerplate planner agent.

    Uses the LLM to break the query into a set of concrete research tasks.
    """
    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def plan(self, query: str) -> Dict[str, List[str]]:
        """
        Use the LLM to produce a deterministic, JSON-structured research plan.

        Expected JSON schema:
        {
          "research_topics": [string, ...],
          "search_queries": [string, ...],
          "analysis_steps": [string, ...]
        }
        """
        system_prompt = (
            "You are a precise AI research planner. Given a user research query, "
            "you must return a JSON object that decomposes the work into topics, "
            "search queries, and analysis steps.\n\n"
            "Requirements:\n"
            "- Respond with VALID JSON only (no markdown, no comments, no extra text).\n"
            "- The top-level object MUST have exactly these keys:\n"
            '  - \"research_topics\": array of strings\n'
            '  - \"search_queries\": array of strings\n'
            '  - \"analysis_steps\": array of strings\n'
            "- Each string should be concise but informative."
        )
        user_content = f"User research query:\n{query}"
        logger.info(f"PlannerAgent: Planning research tasks for query: {query!r}")
        raw = self.llm.chat(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        default_plan: Dict[str, List[str]] = {
            "research_topics": [query],
            "search_queries": [query],
            "analysis_steps": [
                "Review the gathered materials and identify key themes.",
                "Compare and contrast differing viewpoints.",
                "Synthesize findings into a coherent explanation.",
            ],
        }

        try:
            data: Any = json.loads(raw)
            if not isinstance(data, dict):
                return default_plan
            research_topics = data.get("research_topics") or []
            search_queries = data.get("search_queries") or []
            analysis_steps = data.get("analysis_steps") or []

            if not all(isinstance(x, str) for x in research_topics):
                research_topics = default_plan["research_topics"]
            if not all(isinstance(x, str) for x in search_queries):
                search_queries = default_plan["search_queries"]
            if not all(isinstance(x, str) for x in analysis_steps):
                analysis_steps = default_plan["analysis_steps"]

            return {
                "research_topics": research_topics,
                "search_queries": search_queries,
                "analysis_steps": analysis_steps,
            }
        except Exception:
            # Fall back to a simple, deterministic plan if JSON parsing fails
            logger.info("PlannerAgent: Failed to parse JSON plan, using default plan.")
            return default_plan

    def __call__(self, state: ResearchState) -> ResearchState:
        plan = self.plan(state.user_query)
        state.research_topics = plan["research_topics"]
        state.search_queries = plan["search_queries"]
        state.analysis_steps = plan["analysis_steps"]
        logger.info(
            "PlannerAgent: Generated plan with %d topics, %d queries, %d steps.",
            len(state.research_topics),
            len(state.search_queries),
            len(state.analysis_steps),
        )
        return state


