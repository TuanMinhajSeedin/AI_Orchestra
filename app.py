"""
Streamlit UI for AI Research Orchestrator.

Provides a conversational chat interface that calls the FastAPI /research endpoint.
"""

import os
import requests
import streamlit as st


# API endpoint URL (can be configured via environment variable)
API_URL = os.getenv("API_URL", "http://localhost:8000")


def run_research_sync(query: str, api_url: str = None) -> str:
    """
    Call the FastAPI /research endpoint to run the research pipeline.
    
    Args:
        query: Research query string
        api_url: API endpoint URL (defaults to API_URL from environment)
        
    Returns:
        Final report string, or error message if request fails
    """
    if api_url is None:
        api_url = API_URL
    
    try:
        response = requests.post(
            f"{api_url}/research",
            json={"query": query},
            timeout=300,  # 5 minute timeout for long-running research
        )
        response.raise_for_status()
        result = response.json()
        return result.get("final_report", "No report generated.")
    except requests.exceptions.ConnectionError:
        return (
            "❌ **Error: Could not connect to the API server.**\n\n"
            "Please make sure the FastAPI server is running:\n"
            "```bash\nuvicorn app.main:app --reload\n```"
        )
    except requests.exceptions.Timeout:
        return (
            "⏱️ **Error: Request timed out.**\n\n"
            "The research pipeline is taking longer than expected. "
            "Please try again or check the server logs."
        )
    except requests.exceptions.HTTPError as e:
        error_detail = "Unknown error"
        try:
            error_data = e.response.json()
            error_detail = error_data.get("detail", {}).get("message", str(e))
        except Exception:
            error_detail = str(e)
        return f"❌ **Error: {error_detail}**"
    except Exception as e:
        return f"❌ **Unexpected error: {str(e)}**"


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
    
    # Initialize API URL in session state
    if "api_url" not in st.session_state:
        st.session_state.api_url = API_URL
    
    # Show API connection status in sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_url = st.text_input(
            "API URL", 
            value=st.session_state.api_url, 
            help="FastAPI server endpoint"
        )
        st.session_state.api_url = api_url
        
        # Health check
        try:
            health_response = requests.get(f"{st.session_state.api_url}/health", timeout=2)
            if health_response.status_code == 200:
                st.success("✅ API Connected")
            else:
                st.warning("⚠️ API Status Unknown")
        except Exception:
            st.error("❌ API Not Reachable")
            st.info(f"Make sure the server is running at:\n`{st.session_state.api_url}`")

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
                # Use the API URL from session state if available
                api_url = st.session_state.get("api_url", API_URL)
                report = run_research_sync(prompt, api_url=api_url)

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


