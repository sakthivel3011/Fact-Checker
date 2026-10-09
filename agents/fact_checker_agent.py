"""
LangGraph Nodes for the Fact-Checking Multi-Agent Workflow.
"""

from typing import Dict, Any, List
from core.state import FactCheckState, FactCheckVerdict, SourceCitation
from core.safety import evaluate_input_safety, verify_hallucination_and_citations, enforce_credibility_guardrail
from core.react_agent import ReActAgent
from core.llm_provider import get_llm_client
from prompts.fact_check_prompts import FACT_CHECKER_SYSTEM_PROMPT, FEW_SHOT_FACT_CHECK_EXAMPLES
from tools.clickbait import analyze_clickbait
from tools.credibility import compute_aggregate_credibility, get_domain_credibility
from rag.vector_store import vector_store


def input_guardrail_node(state: FactCheckState) -> Dict[str, Any]:
    """Validates user claim against prompt injection and toxic patterns."""
    raw_claim = state.get("raw_claim", "")
    is_safe, reason = evaluate_input_safety(raw_claim)
    return {
        "cleaned_claim": raw_claim.strip(),
        "is_safe": is_safe,
        "safety_notes": reason
    }


def clickbait_analyzer_node(state: FactCheckState) -> Dict[str, Any]:
    """Analyzes sensationalism, all-caps, and exaggerated phrasing."""
    claim = state.get("cleaned_claim", "")
    res = analyze_clickbait(claim)
    return {
        "clickbait_score": res["clickbait_score"],
        "clickbait_flags": res["flags"]
    }


def rag_retrieval_node(state: FactCheckState) -> Dict[str, Any]:
    """Queries RAG vector store for verified benchmark evidence."""
    claim = state.get("cleaned_claim", "")
    hits = vector_store.similarity_search(claim, top_k=3)
    return {
        "rag_evidence": hits
    }


def react_search_node(state: FactCheckState) -> Dict[str, Any]:
    """Executes ReAct deliberation loop with Tavily search."""
    claim = state.get("cleaned_claim", "")
    react_agent = ReActAgent(max_iterations=3)
    steps, evidence = react_agent.execute(claim)
    return {
        "react_thoughts": steps,
        "web_evidence": evidence
    }


def evidence_evaluator_node(state: FactCheckState) -> Dict[str, Any]:
    """Aggregates credibility across all RAG and web sources."""
    web_evidence = state.get("web_evidence", [])
    rag_evidence = state.get("rag_evidence", [])

    all_evidence = list(web_evidence)
    for r in rag_evidence:
        for s in r.get("sources", []):
            all_evidence.append({
                "title": s.get("title", r.get("claim", "")),
                "url": s.get("url", ""),
                "domain": s.get("domain", "rag"),
                "credibility_rating": s.get("credibility_rating", 90),
                "snippet": r.get("content", "")
            })

    agg_score = compute_aggregate_credibility(all_evidence)
    return {
        "credibility_score": agg_score
    }


def verdict_synthesizer_node(state: FactCheckState) -> Dict[str, Any]:
    """Synthesizes all evidence into a structured final verdict."""
    if not state.get("is_safe", True):
        # Return blocked verdict immediately
        verdict_obj = FactCheckVerdict(
            claim=state.get("cleaned_claim", ""),
            verdict="UNVERIFIED",
            credibility_score=0.0,
            confidence=0.0,
            summary="Request rejected by safety guardrail.",
            reasoning=f"The provided input failed safety checks: {state.get('safety_notes', '')}",
            clickbait_score=state.get("clickbait_score", 0.0),
            clickbait_flags=state.get("clickbait_flags", []),
            is_safe=False,
            safety_notes=state.get("safety_notes"),
            sources=[],
            react_steps=state.get("react_thoughts", [])
        )
        return {
            "verdict": verdict_obj.verdict,
            "credibility_score": verdict_obj.credibility_score,
            "confidence": verdict_obj.confidence,
            "summary": verdict_obj.summary,
            "reasoning": verdict_obj.reasoning,
            "final_output": verdict_obj
        }

    claim = state.get("cleaned_claim", "")
    web_evidence = state.get("web_evidence", [])
    rag_evidence = state.get("rag_evidence", [])
    clickbait_score = state.get("clickbait_score", 0.0)

    # Format evidence for prompt
    evidence_text = []
    for idx, e in enumerate(web_evidence[:5], 1):
        evidence_text.append(f"[{idx}] Source: {e.get('domain')} (Credibility: {e.get('credibility_rating')}/100)\nTitle: {e.get('title')}\nExcerpt: {e.get('snippet')[:200]}")

    for idx, r in enumerate(rag_evidence[:3], len(evidence_text) + 1):
        evidence_text.append(f"[{idx}] Known Fact Check: {r.get('claim')}\nOutcome: {r.get('verdict')}\nExplanation: {r.get('content')[:200]}")

    prompt_body = f"""
CLAIM TO VERIFY:
"{claim}"

COLLECTED EVIDENCE:
{chr(10).join(evidence_text) if evidence_text else "No external articles discovered."}

CLICKBAIT SCORE: {clickbait_score}/100

Perform forensic assessment and return structured verdict.
"""

    llm = get_llm_client()
    raw_res = llm.generate_json(
        system_prompt=f"{FACT_CHECKER_SYSTEM_PROMPT}\n{FEW_SHOT_FACT_CHECK_EXAMPLES}",
        user_prompt=prompt_body
    )

    verdict_type = raw_res.get("verdict", "UNVERIFIED")
    cred_score = float(raw_res.get("credibility_score", state.get("credibility_score", 50.0)))
    conf_score = float(raw_res.get("confidence", 75.0))

    # Prepare citations
    citations: List[SourceCitation] = []
    for e in web_evidence[:4]:
        d = e.get("domain", "reuters.com")
        c_rating = e.get("credibility_rating", 85)
        citations.append(SourceCitation(
            title=e.get("title", "News Report"),
            url=e.get("url", "https://" + d),
            domain=d,
            credibility_rating=c_rating,
            snippet=e.get("snippet", "")[:180],
            stance="supports" if verdict_type == "TRUE" else ("refutes" if verdict_type == "FALSE" else "neutral")
        ))

    # Apply safety and hallucination guardrail
    hallucination_check = verify_hallucination_and_citations(
        {"sources": [c.model_dump() for c in citations], "confidence": conf_score},
        web_evidence
    )
    guarded_verdict, guarded_score, _ = enforce_credibility_guardrail(
        verdict_type, cred_score, web_evidence
    )

    final_verdict = FactCheckVerdict(
        claim=claim,
        verdict=guarded_verdict,
        credibility_score=guarded_score,
        confidence=hallucination_check["adjusted_confidence"],
        summary=raw_res.get("summary", "Analysis completed."),
        reasoning=raw_res.get("reasoning", "Evidence synthesized across authoritative sources."),
        clickbait_score=clickbait_score,
        clickbait_flags=state.get("clickbait_flags", []),
        is_safe=True,
        safety_notes=state.get("safety_notes"),
        sources=citations,
        react_steps=state.get("react_thoughts", [])
    )

    return {
        "verdict": final_verdict.verdict,
        "credibility_score": final_verdict.credibility_score,
        "confidence": final_verdict.confidence,
        "summary": final_verdict.summary,
        "reasoning": final_verdict.reasoning,
        "sources": [s.model_dump() for s in final_verdict.sources],
        "final_output": final_verdict
    }
