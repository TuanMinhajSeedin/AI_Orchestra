"""
Chainlit UI for AI Research Orchestrator.

This provides a conversational chat interface similar to SuperWhisper,
with real-time progress indicators showing each step of the research pipeline.
"""

import chainlit as cl
from typing import Optional

from app.orchestrator import Orchestrator
from app.state import ResearchState


# Initialize orchestrator (singleton)
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


def get_status_message(step: str) -> str:
    """Get user-friendly status message for each step."""
    status_messages = {
        "planner": "📋 Planning research strategy",
        "search": "🌐 Searching the internet",
        "analyzer": "🔍 Analyzing search results",
        "summarizer": "📝 Summarizing findings",
        "reporter": "📄 Generating final report",
    }
    return status_messages.get(step, f"⏳ Processing {step}")


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    await cl.Message(
        content="🔍 **AI Research Assistant**\n\n"
                "I can help you conduct comprehensive research on any topic. "
                "Just ask me a research question, and I'll:\n"
                "1. Plan the research strategy\n"
                "2. Search the internet for relevant sources\n"
                "3. Analyze and extract key insights\n"
                "4. Summarize findings\n"
                "5. Generate a comprehensive report\n\n"
                "What would you like to research?",
        author="Assistant"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and run research pipeline."""
    query = message.content.strip()
    
    if not query:
        await cl.Message(
            content="Please provide a research query.",
            author="Assistant"
        ).send()
        return
    
    try:
        # Show user message
        await cl.Message(content=query, author="User").send()

        # Initialize orchestrator
        orchestrator = get_orchestrator()

        # Single status message for pipeline start
        await cl.Message(
            content=(
                "🚀 Starting research pipeline:\n"
                "- 📋 Planner\n"
                "- 🌐 Search\n"
                "- 🔍 Analyzer\n"
                "- 📝 Summarizer\n"
                "- 📄 Report Generator"
            ),
            author="Assistant",
        ).send()

        # Run the full pipeline without streaming to avoid async generator issues
        state = await orchestrator.run_state(query=query)
        
        # Check for errors
        if state.status == "error":
            error_msg = state.error or "Research failed"
            await cl.Message(
                content=f"❌ **Error:** {error_msg}",
                author="Assistant"
            ).send()
        else:
            # Success - show final report
            report = state.final_report or "No report generated."
            
            # Create message with report
            msg = cl.Message(
                content=f"✅ **Research Complete!**\n\n{report}",
                author="Assistant"
            )
            
            # Add PDF file if it was generated
            from pathlib import Path
            from app.tools.pdf_exporter import PDFExporter
            try:
                exporter = PDFExporter()
                pdf_path = Path(exporter.output_dir) / f"{exporter.sanitize_filename(query)}.pdf"
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        await cl.Message(
                            content=f"📄 **PDF Report Generated**\n\n"
                                    f"Your research report has been saved as a PDF.",
                            author="Assistant",
                            attachments=[cl.File(
                                name=pdf_path.name,
                                path=str(pdf_path),
                                mime="application/pdf"
                            )]
                        ).send()
            except Exception:
                pass  # PDF attachment is optional
            
            await msg.send()
            
            # Show research details in a collapsible section
            details = f"""
**Research Details:**

- **Query:** {state.user_query}
- **Status:** {state.status}
- **Search Results:** {len(state.search_results)} found
- **Insights Extracted:** {len(state.extracted_insights)}
"""
            # if state.search_queries:
            #     details += "\n**Search Queries Used:**\n"
            #     for q in state.search_queries:
            #         details += f"- {q}\n"
            
            # await cl.Message(
            #     content=details,
            #     author="Assistant"
            # ).send()
    
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        await cl.Message(
            content=f"❌ **Error:** {error_msg}",
            author="Assistant"
        ).send()
