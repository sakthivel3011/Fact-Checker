"""
LangGraph StateGraph Workflow Orchestrator.
Builds, compiles, and executes multi-agent fact-checking and news-digest graphs.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from core.state import FactCheckState, NewsDigestState, FactCheckVerdict, NewsDigestResult
from agents.fact_checker_agent import (
    input_guardrail_node,
    clickbait_analyzer_node,
    rag_retrieval_node,
    react_search_node,
    evidence_evaluator_node,
    verdict_synthesizer_node
)
from agents.news_digest_agent import (
    fetch_articles_node,
    filter_and_rank_node,
    summarize_articles_node,
    compile_digest_node
)


# -------------------------------------------------------------------------
# Fact-Checking LangGraph Workflow
# -------------------------------------------------------------------------

def check_safety_conditional(state: FactCheckState) -> Literal["proceed", "abort"]:
    """Conditional edge routing based on input safety guardrail."""
    return "proceed" if state.get("is_safe", True) else "abort"


def build_fact_check_graph():
    """Builds and compiles the Fact-Checking LangGraph StateGraph."""
    workflow = StateGraph(FactCheckState)

    # Add Nodes
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("clickbait_analyzer", clickbait_analyzer_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("react_search", react_search_node)
    workflow.add_node("evidence_evaluator", evidence_evaluator_node)
    workflow.add_node("verdict_synthesizer", verdict_synthesizer_node)

    # Add Edges & Conditional Routing
    workflow.add_edge(START, "input_guardrail")
    workflow.add_conditional_edges(
        "input_guardrail",
        check_safety_conditional,
        {
            "proceed": "clickbait_analyzer",
            "abort": "verdict_synthesizer"
        }
    )
    workflow.add_edge("clickbait_analyzer", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "react_search")
    workflow.add_edge("react_search", "evidence_evaluator")
    workflow.add_edge("evidence_evaluator", "verdict_synthesizer")
    workflow.add_edge("verdict_synthesizer", END)

    return workflow.compile()


# -------------------------------------------------------------------------
# News Digest LangGraph Workflow
# -------------------------------------------------------------------------

def build_news_digest_graph():
    """Builds and compiles the Daily News Digest LangGraph StateGraph."""
    workflow = StateGraph(NewsDigestState)

    # Add Nodes
    workflow.add_node("fetch_articles", fetch_articles_node)
    workflow.add_node("filter_and_rank", filter_and_rank_node)
    workflow.add_node("summarize_articles", summarize_articles_node)
    workflow.add_node("compile_digest", compile_digest_node)

    # Add Linear Flow
    workflow.add_edge(START, "fetch_articles")
    workflow.add_edge("fetch_articles", "filter_and_rank")
    workflow.add_edge("filter_and_rank", "summarize_articles")
    workflow.add_edge("summarize_articles", "compile_digest")
    workflow.add_edge("compile_digest", END)

    return workflow.compile()


# Compiled Singleton Graph Instances
fact_check_app = build_fact_check_graph()
news_digest_app = build_news_digest_graph()


# Execution helpers
def run_fact_check(claim: str) -> FactCheckVerdict:
    """Invokes the compiled Fact-Checking LangGraph."""
    initial_state: FactCheckState = {"raw_claim": claim}
    final_state = fact_check_app.invoke(initial_state)
    output = final_state.get("final_output")
    if isinstance(output, FactCheckVerdict):
        return output
    # Fallback instantiation if needed
    return FactCheckVerdict(
        claim=claim,
        verdict=final_state.get("verdict", "UNVERIFIED"),
        credibility_score=final_state.get("credibility_score", 50.0),
        confidence=final_state.get("confidence", 70.0),
        summary=final_state.get("summary", "Analysis completed."),
        reasoning=final_state.get("reasoning", "Evidence synthesized."),
        clickbait_score=final_state.get("clickbait_score", 0.0),
        clickbait_flags=final_state.get("clickbait_flags", []),
        is_safe=final_state.get("is_safe", True),
        react_steps=final_state.get("react_thoughts", [])
    )


def run_news_digest(category: str = "World", limit: int = 5) -> NewsDigestResult:
    """Invokes the compiled News Digest LangGraph."""
    initial_state: NewsDigestState = {"category": category, "limit": limit}
    final_state = news_digest_app.invoke(initial_state)
    output = final_state.get("final_digest")
    if isinstance(output, NewsDigestResult):
        return output
    raise RuntimeError("News digest pipeline failed to produce structured output.")


def get_fact_check_mermaid() -> str:
    """Returns Mermaid diagram string for fact check graph."""
    return """graph TD
    START([START]) --> IG[Input Guardrail Node]
    IG -->|Safe| CA[Clickbait Analyzer Node]
    IG -->|Unsafe / Injected| VS[Verdict Synthesizer Node]
    CA --> RAG[RAG Retrieval Node]
    RAG --> RS[ReAct Search Node Tavily]
    RS --> EE[Evidence Evaluator Node]
    EE --> VS
    VS --> END([END])
"""


def get_news_digest_mermaid() -> str:
    """Returns Mermaid diagram string for news digest graph."""
    return """graph TD
    START([START]) --> FA[Fetch RSS Articles Node]
    FA --> FR[Filter & Rank by Credibility Node]
    FR --> SA[Summarize & Extract Points Node]
    SA --> CD[Compile Digest & Markdown Node]
    CD --> END([END])
"""
