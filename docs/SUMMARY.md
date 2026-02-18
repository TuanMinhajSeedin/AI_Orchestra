# AI Research Orchestrator - One Page Summary

## What It Is
A multi-agent AI system that automates end-to-end research workflows. Given a research query, it plans, searches, analyzes, summarizes, and generates structured research reports using specialized AI agents orchestrated by LangGraph.

## Core Concept
**Multi-Agent Pipeline**: Five specialized agents collaborate through a shared state object:
1. **Planner** → Breaks query into topics, search queries, and analysis steps
2. **Web Search** → Retrieves web content via Serper API and indexes into FAISS vector store
3. **Analyzer** → Extracts structured insights (findings, evidence, sources)
4. **Summarizer** → Generates 300-500 word academic summary
5. **Report Generator** → Creates comprehensive markdown report with 7 sections

## Key Technologies
- **LangGraph**: Stateful orchestration with conditional routing and retry logic
- **OpenAI API**: GPT-4 for agents, text-embedding-3-small for embeddings
- **FAISS**: In-memory vector store for similarity search
- **Serper API**: Web search integration
- **FastAPI**: REST API backend
- **Streamlit**: Conversational chat UI
- **Pydantic**: Type-safe state management

## Architecture Flow
```
User Query → Planner → Web Search → Analyzer → Summarizer → Report Generator → Markdown File
                ↓           ↓           ↓
            (Retry if    (Retry if   (Error if
             empty)      empty)      no insights)
```

## State Management
Shared `ResearchState` object flows through all agents, containing:
- User query, research topics, search queries
- Search results (title, source, content, URL)
- Extracted insights (finding, evidence, source)
- Summary, final report, status, error messages

## Conditional Logic
- **Search Retry**: Automatically retries if no results found (max 2 attempts)
- **Error Handling**: Stops pipeline if no insights extracted
- **State Tracking**: Status field tracks: pending → running → completed/error

## Output
- **Format**: Structured markdown report
- **Sections**: Introduction, Background, Key Findings, Trends, Challenges, Conclusion, References
- **Location**: `output/{sanitized_query}.md`
- **Logging**: Console + `logs/runing_logs.log` (UTF-8)

## Quick Start
1. Install: `pip install -r requirements.txt`
2. Configure: Create `.env` with `OPENAI_API_KEY` and `SERPER_API_KEY`
3. Run UI: `streamlit run app.py`
4. Run API: `uvicorn app.main:app --reload`

## Project Structure
```
app/
  ├── orchestrator.py      # LangGraph graph definition
  ├── state.py             # ResearchState Pydantic model
  ├── agents/              # 5 specialized agents
  └── tools/               # Web search, URL loader, vector store
```

## Key Features
✅ **Intelligent Planning**: LLM-based query decomposition  
✅ **Web Search Integration**: Serper API + content extraction  
✅ **Vector Store**: FAISS indexing for future RAG capabilities  
✅ **Structured Output**: Consistent markdown report format  
✅ **Error Recovery**: Automatic retry logic for failed searches  
✅ **Dual Interface**: Streamlit UI + FastAPI REST endpoint  
✅ **Comprehensive Logging**: File + console logging with timestamps  

## Use Cases
- Academic research assistance
- Market research automation
- Competitive intelligence gathering
- Technical documentation research
- News and trend analysis

## Limitations
- Vector store is in-memory (not persisted)
- No real-time progress updates in UI (single spinner)
- Limited to web search sources (no database integration)
- No citation validation or fact-checking agents

## Future Enhancements
- Persistent vector store (save/load FAISS index)
- Real-time progress indicators per agent
- Additional agents (fact-checker, citation validator)
- Voice input integration
- Multi-source data integration (databases, APIs)

---


