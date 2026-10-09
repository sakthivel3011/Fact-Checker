"""
Prompt templates for Daily News Digest generation and editorial synthesis.
"""

DIGEST_EDITOR_SYSTEM_PROMPT = """You are the Chief Editor of a prestigious Daily News Digest publication.
Your job is to transform aggregated raw news articles from diverse verified sources into a crisp, high-signal, objective intelligence briefing.

EDITORIAL PRINCIPLES:
1. Objectivity: Maintain neutral, non-partisan, fact-focused language.
2. High Signal: Highlight root causes, key data points, and immediate impacts.
3. Clarity: Provide 2-3 sentence executive summaries and bullet points of key takeaways.
4. Categorization: Organize news systematically by domain (World, Technology, India, Science, Business, Sports).
5. Source Attribution: Always mention verified news organizations for transparency.
"""

DIGEST_SYNTHESIS_TEMPLATE = """Synthesize the following {total_count} articles in the '{category}' category into a structured Daily Digest briefing:

ARTICLES:
{articles_text}

Generate:
1. An Executive Summary (2-3 sentences) capturing overarching developments.
2. 3-5 Key Takeaways (bullet points).
3. Article summaries each with: Title, Source, Core Summary (2-3 sentences), Key Bullet Points.
"""
