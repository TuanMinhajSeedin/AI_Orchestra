"""
Streamlit UI for AI Research Orchestrator.

Provides a conversational chat interface with a spinner while the
LangGraph-based pipeline runs.
"""

import asyncio

import streamlit as st

from app.orchestrator import Orchestrator


# Initialize orchestrator (cached across reruns)
@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator()


def run_research_sync(query: str) -> str:
    """
    Run the async orchestrator.run(query) from a synchronous context.
    """
    orchestrator = get_orchestrator()

    # Use a fresh event loop for each call to avoid conflicts
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        report = loop.run_until_complete(orchestrator.run(query=query))
    finally:
        loop.close()
        asyncio.set_event_loop(None)

    return report


def main() -> None:
    st.set_page_config(
        page_title="AI Research Assistant",
        page_icon="🔍",
        layout="wide",
    )

    st.title("🔍 AI Research Assistant")
    st.markdown(
        "Ask a research question and I'll plan, search, analyze, "
        "summarize, and generate a structured report for you."
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Enter your research query..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant "spinner" while pipeline runs
        with st.chat_message("assistant"):
            with st.spinner(
                "🚀 Running research pipeline: planner → search → analyzer → summarizer → report..."
            ):
                report = run_research_sync(prompt)

            # Show the final report
            st.markdown(report or "No report generated.")

        # Save assistant response to history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": report or "No report generated.",
            }
        )


if __name__ == "__main__":
    main()


