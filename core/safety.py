"""
Safety Guardrails and Hallucination Verification.
Protects against prompt injections, toxic/adversarial queries, and LLM hallucinations.
"""

import re
from typing import Dict, Any, List, Tuple
from tools.credibility import extract_domain


# Known prompt injection & adversarial trigger patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?guidelines",
    r"you\s+are\s+now\s+in\s+dan\s+mode",
    r"system\s*prompt\s*leak",
    r"<script[\s>]",
    r"drop\s+table\s+",
    r"bypass\s+safety\s+filter",
]


def evaluate_input_safety(text: str) -> Tuple[bool, str]:
    """
    Validates user claim against prompt injection and malicious adversarial inputs.
    Returns (is_safe, reason_or_notes).
    """
    if not text or not text.strip():
        return False, "Empty or whitespace-only input provided."

    lower_text = text.lower()

    # Check length limits
    if len(text) > 4000:
        return False, "Input exceeds maximum character length limit (4000 chars)."

    # Check injection patterns
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower_text):
            return False, f"Potential adversarial prompt injection detected matching pattern: {pattern}"

    return True, "Input passed safety guardrail verification."


def verify_hallucination_and_citations(
    verdict: Dict[str, Any],
    retrieved_evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verifies that sources and statements cited in the final verdict
    actually originate from the retrieved RAG or Web evidence, preventing hallucinations.
    """
    verified_sources: List[Dict[str, Any]] = []
    hallucination_flags: List[str] = []

    # Build lookup of valid retrieved domains and URLs
    valid_domains = set()
    for item in retrieved_evidence:
        d = extract_domain(item.get("url", "")) or extract_domain(item.get("domain", ""))
        if d:
            valid_domains.add(d)

    # Validate each source claimed by the synthesizer
    claimed_sources = verdict.get("sources", [])
    for src in claimed_sources:
        src_domain = extract_domain(src.get("url", "")) or extract_domain(src.get("domain", ""))
        
        # Check if source domain was part of verified evidence
        is_grounded = any(
            src_domain in valid_d or valid_d in src_domain 
            for valid_d in valid_domains
        ) if valid_domains else True

        if is_grounded:
            verified_sources.append(src)
        else:
            hallucination_flags.append(
                f"Source '{src.get('domain', src.get('title', 'Unknown'))}' was not grounded in retrieved evidence."
            )

    # Check for hallucination penalty
    adjusted_confidence = float(verdict.get("confidence", 80.0))
    if hallucination_flags:
        adjusted_confidence = max(20.0, adjusted_confidence - (len(hallucination_flags) * 15.0))

    return {
        "verified_sources": verified_sources if verified_sources else claimed_sources,
        "hallucination_flags": hallucination_flags,
        "adjusted_confidence": round(adjusted_confidence, 1),
        "is_grounded": len(hallucination_flags) == 0
    }


def enforce_credibility_guardrail(
    verdict_type: str,
    credibility_score: float,
    evidence_items: List[Dict[str, Any]]
) -> Tuple[str, float, str]:
    """
    Ensures a claim cannot be classified as TRUE if backed solely by low-credibility or satire outlets.
    """
    if not evidence_items:
        return "UNVERIFIED", 50.0, "Insufficient verifiable evidence discovered."

    has_trusted = any(item.get("credibility_rating", 50) >= 80 for item in evidence_items)
    is_all_satire = all(item.get("domain") in ["theonion.com", "babylonbee.com"] for item in evidence_items if "domain" in item)

    if is_all_satire:
        return "FALSE", 10.0, "Claim originated exclusively from known satire publication."

    if verdict_type in ["TRUE", "LIKELY TRUE"] and not has_trusted:
        # Downgrade if no reputable source confirms it
        return "UNVERIFIED", min(credibility_score, 55.0), "Downgraded due to lack of high-tier primary confirmation."

    return verdict_type, credibility_score, "Passed credibility guardrail."
