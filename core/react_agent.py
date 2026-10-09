"""
ReAct (Reasoning + Acting) Agent Execution Engine.
Executes an explicit Thought -> Action -> Observation loop with Tavily search and RAG retrieval.
"""

import json
from typing import Dict, Any, List, Tuple
from config import settings
from tools.tavily_search import tavily_search
from tools.credibility import get_domain_credibility
from tools.clickbait import analyze_clickbait
from rag.vector_store import vector_store


class ReActAgent:
    """
    ReAct deliberative agent that decides what evidence to collect
    through multi-step tool execution.
    """

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations

    def execute(self, claim: str) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:
        """
        Runs the ReAct loop for the specified claim.
        Returns:
            - steps: List of Thought-Action-Observation traces
            - accumulated_evidence: List of evidence items gathered across tools
        """
        steps: List[Dict[str, str]] = []
        accumulated_evidence: List[Dict[str, Any]] = []

        # Step 1: Initial RAG knowledge base check
        step_1_thought = f"Analyze internal verified fact registry for existing benchmark matches regarding '{claim[:60]}'."
        rag_hits = vector_store.similarity_search(claim, top_k=2)

        obs_1 = (
            f"Found {len(rag_hits)} relevant records in verified knowledge base." 
            if rag_hits else "No exact match found in pre-indexed knowledge base."
        )
        steps.append({
            "iteration": 1,
            "thought": step_1_thought,
            "action": "query_rag_database",
            "action_input": claim[:80],
            "observation": obs_1
        })
        for hit in rag_hits:
            for s in hit.get("sources", []):
                accumulated_evidence.append({
                    "title": s.get("title", hit.get("claim", "")),
                    "url": s.get("url", ""),
                    "domain": s.get("domain", "knowledge_base"),
                    "credibility_rating": s.get("credibility_rating", 90),
                    "snippet": hit.get("content", ""),
                    "source_type": "rag_knowledge_base"
                })

        # Step 2: Live Tavily Web Search corroboration
        step_2_thought = f"Search live authoritative web news wire reports via Tavily search for: '{claim[:60]}'."
        web_hits = tavily_search(claim, max_results=3)

        obs_2 = f"Retrieved {len(web_hits)} external reporting sources via Tavily search."
        steps.append({
            "iteration": 2,
            "thought": step_2_thought,
            "action": "tavily_web_search",
            "action_input": f"fact check {claim[:60]}",
            "observation": obs_2
        })
        accumulated_evidence.extend(web_hits)

        # Step 3: Domain Credibility & Sensationalism Cross-Check
        step_3_thought = "Assess source credibility distributions and inspect claim for sensationalist clickbait."
        clickbait_res = analyze_clickbait(claim)
        high_cred_count = sum(1 for e in accumulated_evidence if e.get("credibility_rating", 50) >= 85)

        obs_3 = (
            f"Identified {high_cred_count} Tier-1 credible sources. "
            f"Clickbait score: {clickbait_res['clickbait_score']}/100."
        )
        steps.append({
            "iteration": 3,
            "thought": step_3_thought,
            "action": "credibility_and_clickbait_audit",
            "action_input": claim[:60],
            "observation": obs_3
        })

        return steps, accumulated_evidence
