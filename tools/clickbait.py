"""
Clickbait & Sensationalism Detection Tool.
Identifies sensational language, exaggerated claims, and clickbait patterns in headlines and claims.
"""

import re
from typing import Dict, Any, List

CLICKBAIT_PATTERNS = [
    (r"\b(you won'?t believe|won'?t believe what happened)\b", "Curiosity baiting phrase"),
    (r"\b(what happened next|the reason will shock you)\b", "Dramatic cliffhanger pattern"),
    (r"\b(doctors? (hate|stunned|speechless)|secret cure|miracle cure)\b", "Miracle / pseudo-medical trope"),
    (r"\b(this (one|simple) trick|hidden secret)\b", "Exploitative quick-fix pattern"),
    (r"\b(blow your mind|mind[- ]blowing|insane|shocking|jaw[- ]dropping)\b", "Hyperbolic sensationalism"),
    (r"\b(they don'?t want you to know|conspiracy exposed|truth behind)\b", "Conspiratorial framing"),
    (r"\b(everyone is talking about|breaking internet|viral sensation)\b", "Bandwagon hype"),
]

CLICKBAIT_KEYWORDS = [
    "unbelievable", "bombshell", "bizarre", "catastrophic", "miracle", 
    "explosive", "leaked", "destroyed", "terrifying", "unreal"
]


def analyze_clickbait(text: str) -> Dict[str, Any]:
    """
    Analyzes input claim or headline for clickbait characteristics.
    Returns:
        - clickbait_score: float (0.0 to 100.0)
        - flags: List[str] with specific detected patterns
        - is_clickbait: bool
        - cleaned_summary: normalized text recommendation
    """
    if not text or not text.strip():
        return {
            "clickbait_score": 0.0,
            "flags": [],
            "is_clickbait": False,
            "cleaned_summary": ""
        }

    raw = text.strip()
    flags: List[str] = []
    score = 0.0

    # 1. Excessive Capitalization Check
    words = [w for w in re.findall(r"[A-Za-z]+", raw) if len(w) > 1]
    if words:
        caps_words = [w for w in words if w.isupper() and w not in ["NASA", "WHO", "AI", "FBI", "UK", "USA", "COVID", "RSS", "PM", "CEO"]]
        caps_ratio = len(caps_words) / len(words)
        if caps_ratio > 0.3:
            score += 25.0
            flags.append(f"Excessive ALL-CAPS words ({len(caps_words)} words flagged)")
        elif len(caps_words) >= 2:
            score += 15.0
            flags.append(f"Capitalized emotional emphasis ({', '.join(caps_words[:3])})")

    # 2. Excessive Punctuation Check (!, ?, ?!)
    if re.search(r"!{2,}|\?{2,}|!\?|\?!", raw):
        score += 20.0
        flags.append("Excessive emotional punctuation (e.g., '!!' or '??')")
    elif raw.endswith("!"):
        score += 8.0
        flags.append("Sensational exclamation ending")

    # 3. Clickbait regex pattern matches
    lower_text = raw.lower()
    for pattern, description in CLICKBAIT_PATTERNS:
        if re.search(pattern, lower_text):
            score += 20.0
            flags.append(description)

    # 4. Sensational keyword presence
    found_keywords = [kw for kw in CLICKBAIT_KEYWORDS if re.search(rf"\b{kw}\b", lower_text)]
    if found_keywords:
        score += min(len(found_keywords) * 10.0, 25.0)
        flags.append(f"Sensationalist buzzwords detected: {', '.join(found_keywords)}")

    # 5. Numerical curiosity hooks (e.g., "7 reasons why...")
    if re.search(r"^\d+\s+(reasons|ways|things|secrets|tricks)\b", lower_text):
        score += 15.0
        flags.append("Numbered listicle curiosity hook")

    final_score = min(round(score, 1), 100.0)
    is_clickbait = final_score >= 40.0

    return {
        "clickbait_score": final_score,
        "flags": flags,
        "is_clickbait": is_clickbait,
        "cleaned_summary": "Headline presents objective factual language" if not is_clickbait else "Headline uses sensationalized wording designed to elicit emotional reaction"
    }
