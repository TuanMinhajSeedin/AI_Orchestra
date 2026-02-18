from typing import List, Dict, Any
import json
import logging

from app.state import ResearchState
from app.llm import LLM


logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """
    AnalyzerAgent

    Goal (STEP 5): Extract structured insights from raw search content.

    Input:  search_results (list of dicts from WebSearchAgent)
    Output: extracted_insights as a list of objects:
        {
          "finding": str,
          "evidence": str,
          "source": str
        }
    """

    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def _analyze_single(self, idx: int, item: Dict[str, Any]) -> List[Dict[str, str]]:
        content = item.get("content") or item.get("snippet") or ""
        if not content:
            return []
        source = item.get("source") or item.get("url") or "unknown"
        truncated = content[:2000]

        system_prompt = (
            "You are an AI research analyst. For the given text snippet, "
            "extract key findings, statistics, methodologies, and trends.\n\n"
            "Return a JSON array of objects with this exact schema:\n"
            '[\n'
            '  {\n'
            '    \"finding\": string,   // main finding or insight\n'
            '    \"evidence\": string,  // brief quote or paraphrase from the text\n'
            '    \"source\": string     // short source identifier\n'
            '  }\n'
            "]\n\n"
            "Rules:\n"
            "- Respond with VALID JSON ONLY (no markdown, no comments, no extra text).\n"
            "- If there are no meaningful findings, return an empty JSON array []."
        )
        user_content = f"Snippet {idx} (source={source}):\n{truncated}"
        raw = self.llm.chat(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                return []
            cleaned: List[Dict[str, str]] = []
            for obj in data:
                if not isinstance(obj, dict):
                    continue
                finding = str(obj.get("finding", "")).strip()
                evidence = str(obj.get("evidence", "")).strip()
                src = str(obj.get("source", source)).strip() or source
                if not finding:
                    continue
                cleaned.append(
                    {
                        "finding": finding,
                        "evidence": evidence,
                        "source": src,
                    }
                )
            return cleaned
        except Exception:
            return []

    def analyze(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        if not search_results:
            return []

        insights: List[Dict[str, str]] = []
        for idx, item in enumerate(search_results, start=1):
            insights.extend(self._analyze_single(idx, item))
        logger.info("AnalyzerAgent: Extracted %d structured insights.", len(insights))
        return insights

    def __call__(self, state: ResearchState) -> ResearchState:
        insights = self.analyze(state.search_results)
        state.extracted_insights = insights
        if not insights:
            state.status = "error"
            state.error = "Analyzer produced no insights from the search results."
            logger.info("AnalyzerAgent: No insights extracted; marking error state.")
        return state


