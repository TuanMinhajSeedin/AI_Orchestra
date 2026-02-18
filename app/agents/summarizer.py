from typing import List, Dict
import logging

from app.state import ResearchState
from app.llm import LLM


logger = logging.getLogger(__name__)


class SummarizerAgent:
    """
    Boilerplate summarizer agent.

    Uses the LLM to compress analyses into a concise,
    high-level summary tailored to the original query.
    """
    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def summarize(self, query: str, insights: List[Dict[str, str]]) -> str:
        if not insights:
            return "No analyses available to summarize yet."
        # Convert structured insights into a readable bullet list for the LLM.
        lines: List[str] = []
        for insight in insights:
            finding = insight.get("finding", "")
            evidence = insight.get("evidence", "")
            source = insight.get("source", "")
            line = f"- Finding: {finding}"
            if evidence:
                line += f" | Evidence: {evidence}"
            if source:
                line += f" | Source: {source}"
            lines.append(line)
        joined = "\n".join(lines)
        truncated = joined[:6000]
        system_prompt = (
            "You are an expert academic writer. Given a user research query "
            "and a set of structured findings, write a neutral, academic-style "
            "summary.\n\n"
            "Requirements:\n"
            "- Length: 300–500 words.\n"
            "- Tone: neutral, objective, third-person.\n"
            "- Structure: 2–4 clear paragraphs (no bullet lists).\n"
            "- Include: key findings, important statistics, methodologies, and "
            "any notable trends or limitations.\n"
            "- Do NOT invent facts that are not supported by the findings."
        )
        user_content = (
            f"User query:\n{query}\n\nStructured findings:\n{truncated}\n\n"
            "Write the final summary for the user following the requirements."
        )
        summary = self.llm.chat(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        ).strip()
        logger.info("SummarizerAgent: Generated summary of length %d characters.", len(summary))
        return summary

    def __call__(self, state: ResearchState) -> ResearchState:
        state.summary = self.summarize(state.user_query, state.extracted_insights)
        return state


