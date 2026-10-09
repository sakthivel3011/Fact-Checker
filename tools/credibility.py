"""
Source Credibility Scoring Tool.
Evaluates the domain credibility of news sources and fact-checking organizations.
"""

import re
from urllib.parse import urlparse
from typing import Dict, Any, List
from config import settings


def extract_domain(url_or_domain: str) -> str:
    """Extract clean base domain from a URL or raw domain string."""
    if not url_or_domain:
        return ""
    
    url = url_or_domain.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.split(":")[0]  # strip port
        # Strip common subdomains like www, m, mobile, feeds, news
        netloc = re.sub(r"^(www\.|m\.|mobile\.|feeds\.|news\.)", "", netloc)
        return netloc
    except Exception:
        return url_or_domain.lower()


def get_domain_credibility(url_or_domain: str) -> Dict[str, Any]:
    """
    Look up credibility score and classification for a domain or URL.
    Returns credibility score (0-100), tier, and category tags.
    """
    domain = extract_domain(url_or_domain)
    
    # Check exact match or suffix match in configured scores
    score = settings.DOMAIN_CREDIBILITY_SCORES.get(domain)
    if score is None:
        # Check if domain ends with any known key (e.g. news.reuters.com -> reuters.com)
        for known_domain, known_score in settings.DOMAIN_CREDIBILITY_SCORES.items():
            if domain.endswith("." + known_domain) or domain == known_domain:
                score = known_score
                break
    
    # Default score for unknown domains: 65 (moderate neutral)
    if score is None:
        # Give slight boost to academic or government domains
        if domain.endswith((".edu", ".gov", ".org")):
            score = 88
        else:
            score = 65

    # Determine classification tier
    if score >= 90:
        tier = "High Credibility (Primary Source / Verified Fact-Checker)"
        flag = "TRUSTED"
    elif score >= 75:
        tier = "Reliable Mainstream News Source"
        flag = "RELIABLE"
    elif score >= 55:
        tier = "Moderate Reliability (Secondary / Blog / Aggregator)"
        flag = "MODERATE"
    elif score >= 35:
        tier = "Low Reliability / Sensationalist / Tabloid"
        flag = "QUESTIONABLE"
    else:
        tier = "Disreputable / Satire / Propaganda"
        flag = "UNRELIABLE"

    is_satire = domain in ["theonion.com", "babylonbee.com", "clickhole.com"]

    return {
        "domain": domain,
        "score": score,
        "tier": tier,
        "flag": flag,
        "is_satire": is_satire,
        "is_fact_checker": domain in ["snopes.com", "politifact.com", "factcheck.org"]
    }


def compute_aggregate_credibility(evidence_items: List[Dict[str, Any]]) -> float:
    """
    Computes a weighted average credibility score across multiple evidence sources.
    Higher weighted for fact-checkers and wire services.
    """
    if not evidence_items:
        return 50.0  # Default neutral when no evidence exists

    total_weight = 0.0
    weighted_score = 0.0

    for item in evidence_items:
        url = item.get("url", "")
        info = get_domain_credibility(url)
        score = info["score"]

        # Higher weight for established primary/fact-check sources
        weight = 1.5 if info["is_fact_checker"] else (1.2 if score >= 90 else 1.0)
        
        weighted_score += score * weight
        total_weight += weight

    return round(weighted_score / total_weight, 1) if total_weight > 0 else 50.0
