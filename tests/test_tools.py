"""Unit tests for tool modules: credibility, clickbait, rss_fetcher, and tavily_search."""

import pytest
from tools.credibility import get_domain_credibility, extract_domain, compute_aggregate_credibility
from tools.clickbait import analyze_clickbait
from tools.rss_fetcher import fetch_articles_by_category
from tools.tavily_search import tavily_search


def test_extract_domain():
    assert extract_domain("https://www.reuters.com/world/news") == "reuters.com"
    assert extract_domain("http://feeds.bbci.co.uk/news") == "bbci.co.uk"
    assert extract_domain("thehindu.com") == "thehindu.com"


def test_credibility_high_sources():
    reuters_info = get_domain_credibility("reuters.com")
    assert reuters_info["score"] >= 90
    assert reuters_info["flag"] == "TRUSTED"
    assert not reuters_info["is_satire"]

    snopes_info = get_domain_credibility("https://snopes.com/fact-check")
    assert snopes_info["is_fact_checker"] is True


def test_credibility_satire_sources():
    onion_info = get_domain_credibility("theonion.com")
    assert onion_info["is_satire"] is True
    assert onion_info["score"] <= 30


def test_aggregate_credibility():
    evidence = [
        {"url": "https://reuters.com/article", "domain": "reuters.com"},
        {"url": "https://who.int/report", "domain": "who.int"}
    ]
    agg = compute_aggregate_credibility(evidence)
    assert agg >= 90.0


def test_clickbait_detection_sensational():
    sensational = "SHOCKING SECRET REVEALED: YOU WON'T BELIEVE WHAT HAPPENED NEXT!!!"
    res = analyze_clickbait(sensational)
    assert res["is_clickbait"] is True
    assert res["clickbait_score"] >= 50.0
    assert len(res["flags"]) > 0


def test_clickbait_detection_neutral():
    neutral = "The central bank reported a 0.25 percent adjustment in benchmark interest rates."
    res = analyze_clickbait(neutral)
    assert res["is_clickbait"] is False
    assert res["clickbait_score"] <= 20.0


def test_rss_fetcher_fallback():
    articles = fetch_articles_by_category("Technology", limit=2)
    assert len(articles) >= 1
    assert "title" in articles[0]
    assert "url" in articles[0]
    assert articles[0]["credibility_score"] > 0


def test_tavily_search():
    results = tavily_search("quantum computing error correction", max_results=2)
    assert len(results) >= 1
    assert "title" in results[0]
    assert "snippet" in results[0]
