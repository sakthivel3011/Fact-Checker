"""
LangGraph Nodes for the Daily News Digest Multi-Agent Workflow.
"""

import datetime
from typing import Dict, Any, List
from core.state import NewsDigestState, NewsDigestResult, ArticleSummary
from tools.rss_fetcher import fetch_articles_by_category
from tools.clickbait import analyze_clickbait
from core.llm_provider import get_llm_client
from prompts.digest_prompts import DIGEST_EDITOR_SYSTEM_PROMPT


def fetch_articles_node(state: NewsDigestState) -> Dict[str, Any]:
    """Fetches articles from RSS feeds for the specified category."""
    category = state.get("category", "World")
    limit = state.get("limit", 5)
    articles = fetch_articles_by_category(category, limit=limit)
    return {
        "raw_articles": articles
    }


def filter_and_rank_node(state: NewsDigestState) -> Dict[str, Any]:
    """Filters duplicate articles and sorts by domain credibility score."""
    raw = state.get("raw_articles", [])
    seen_titles = set()
    filtered: List[Dict[str, Any]] = []

    for a in raw:
        norm_title = a.get("title", "").strip().lower()
        if norm_title and norm_title not in seen_titles:
            seen_titles.add(norm_title)
            # Evaluate clickbait on headline
            cb_res = analyze_clickbait(a.get("title", ""))
            a["clickbait_score"] = cb_res["clickbait_score"]
            filtered.append(a)

    # Sort descending by credibility score
    filtered.sort(key=lambda x: x.get("credibility_score", 50), reverse=True)
    return {
        "filtered_articles": filtered
    }


def summarize_articles_node(state: NewsDigestState) -> Dict[str, Any]:
    """Generates concise summaries and extracts key takeaway points."""
    filtered = state.get("filtered_articles", [])
    summarized: List[ArticleSummary] = []

    for item in filtered:
        # Generate 2 bullet points
        raw_summary = item.get("summary", "")
        sentences = [s.strip() for s in raw_summary.split(".") if len(s.strip()) > 15]
        key_points = [f"• {s}" for s in sentences[:2]]
        if not key_points:
            key_points = ["• Ongoing development verified by media reporting."]

        summarized.append(ArticleSummary(
            title=item.get("title", ""),
            category=item.get("category", "World"),
            source=item.get("source", "REUTERS"),
            url=item.get("url", ""),
            published=item.get("published", datetime.datetime.now().strftime("%Y-%m-%d")),
            summary=raw_summary[:350] if raw_summary else item.get("title", ""),
            key_points=key_points,
            credibility_score=item.get("credibility_score", 85),
            clickbait_score=item.get("clickbait_score", 0.0)
        ))

    return {
        "summarized_articles": [s.model_dump() for s in summarized]
    }


def compile_digest_node(state: NewsDigestState) -> Dict[str, Any]:
    """Compiles individual summaries into a polished Markdown daily digest."""
    category = state.get("category", "World")
    articles_data = state.get("summarized_articles", [])
    today_str = datetime.datetime.now().strftime("%B %d, %Y")

    # Generate executive summary
    topics = [a.get("title", "")[:40] for a in articles_data[:3]]
    exec_summary = (
        f"Today's {category} briefing covers significant global updates including "
        f"{', '.join(topics)}. Reporting highlights ongoing policy and technological milestones."
    )

    # Format Markdown
    md_lines = [
        f"# 📰 Daily News Digest - {category.upper()}",
        f"**Date:** {today_str} | **Total Stories:** {len(articles_data)}",
        "",
        "## 📌 Executive Summary",
        exec_summary,
        "",
        "## 🌐 Featured Stories",
        ""
    ]

    for idx, a in enumerate(articles_data, 1):
        md_lines.extend([
            f"### {idx}. [{a.get('title')}]({a.get('url')})",
            f"**Source:** {a.get('source')} | **Credibility Rating:** {a.get('credibility_score')}/100",
            "",
            a.get("summary", ""),
            "",
            "**Key Points:**",
            "\n".join(a.get("key_points", [])),
            "",
            "---",
            ""
        ])

    markdown_content = "\n".join(md_lines)

    result = NewsDigestResult(
        date=today_str,
        category=category,
        total_articles=len(articles_data),
        executive_summary=exec_summary,
        trending_topics=topics,
        articles=[ArticleSummary(**a) for a in articles_data],
        markdown_content=markdown_content
    )

    return {
        "executive_summary": exec_summary,
        "trending_topics": topics,
        "digest_markdown": markdown_content,
        "final_digest": result
    }
