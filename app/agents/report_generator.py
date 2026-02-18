from typing import List, Dict
import logging
import re
from pathlib import Path

from app.state import ResearchState
from app.llm import LLM


logger = logging.getLogger(__name__)


class ReportGeneratorAgent:
    """
    ReportGeneratorAgent

    Uses LLM to generate a comprehensive research report from the gathered insights.

    Input:
      - user_query
      - summary
      - extracted_insights
      - search_results

    Output:
      - final_report: markdown-formatted structured research report
        with sections:
          1. Introduction
          2. Background
          3. Key Findings
          4. Trends
          5. Challenges
          6. Conclusion
          7. References
    """

    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename.

        Removes or replaces invalid characters for filenames.
        """
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        filename = filename.strip(" .")
        if len(filename) > 200:
            filename = filename[:200]
        if not filename:
            filename = "research_report"
        return filename

    def generate_report(self, state: ResearchState) -> str:
        """
        Use LLM to generate a comprehensive research report.
        """
        # Prepare insights for the prompt
        insights_text = ""
        if state.extracted_insights:
            insights_lines = []
            for idx, insight in enumerate(state.extracted_insights, start=1):
                finding = insight.get("finding", "")
                evidence = insight.get("evidence", "")
                source = insight.get("source", "")
                line = f"{idx}. **Finding:** {finding}"
                if evidence:
                    line += f"\n   **Evidence:** {evidence}"
                if source:
                    line += f"\n   **Source:** {source}"
                insights_lines.append(line)
            insights_text = "\n\n".join(insights_lines)
        else:
            insights_text = "No insights were extracted from the available sources."

        # Prepare search results summary for references
        references_text = ""
        if state.search_results:
            ref_lines = []
            seen = set()
            for item in state.search_results:
                title = str(item.get("title") or "Untitled Source")
                url = str(item.get("url") or "")
                key = (title, url)
                if key in seen:
                    continue
                seen.add(key)
                if url:
                    ref_lines.append(f"- [{title}]({url})")
                else:
                    ref_lines.append(f"- {title}")
            references_text = "\n".join(ref_lines)
        else:
            references_text = "- No references available."

        # Prepare research topics and search queries context
        topics_text = "\n".join([f"- {topic}" for topic in state.research_topics]) if state.research_topics else "N/A"
        queries_text = "\n".join([f"- {q}" for q in state.search_queries]) if state.search_queries else "N/A"

        system_prompt = (
            "You are an expert research report writer. Your task is to create a "
            "comprehensive, well-structured research report in markdown format.\n\n"
            "The report MUST include the following sections in this exact order:\n"
            "1. Introduction\n"
            "2. Background\n"
            "3. Key Findings\n"
            "4. Trends\n"
            "5. Challenges\n"
            "6. Conclusion\n"
            "7. References\n\n"
            "Requirements:\n"
            "- Write in a professional, academic style\n"
            "- Use proper markdown formatting (headers, lists, emphasis)\n"
            "- Be thorough but concise\n"
            "- Base all content on the provided insights and summary\n"
            "- For the References section, use the exact markdown format provided\n"
            "- Do NOT invent facts not supported by the provided information"
        )

        user_content = f"""Research Query: {state.user_query}

Research Topics Identified:
{topics_text}

Search Queries Used:
{queries_text}

Extracted Insights:
{insights_text}

Summary:
{state.summary or "No summary available."}

References (use exactly as provided):
{references_text}

Please generate a complete research report following the required structure.
The report should be comprehensive, well-written, and based entirely on the 
information provided above."""

        logger.info("ReportGeneratorAgent: Generating report using LLM...")
        report = self.llm.chat(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        ).strip()

        # Ensure the report starts with the title
        if not report.startswith("#"):
            report = "# Research Report\n\n" + report

        logger.info("ReportGeneratorAgent: Report generated successfully (length: %d chars).", len(report))
        return report

    def __call__(self, state: ResearchState) -> ResearchState:
        state.final_report = self.generate_report(state)
        logger.info("ReportGeneratorAgent: Final report generated.")

        # Save report as a markdown file in output/{user_query}.md
        try:
            output_dir = Path("output")
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = self._sanitize_filename(state.user_query) + ".md"
            file_path = output_dir / filename
            file_path.write_text(state.final_report, encoding="utf-8")
            logger.info("ReportGeneratorAgent: Markdown report saved to: %s", file_path)
        except Exception as exc:
            # Don't fail the pipeline if saving markdown fails
            logger.warning("ReportGeneratorAgent: Failed to save markdown report: %s", exc)

        return state


