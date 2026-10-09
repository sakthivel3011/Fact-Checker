"""
Configuration settings for Fact-Checker & Daily News Digest.
Uses environment variables with intelligent fallbacks.
"""

import os
from pathlib import Path
from typing import Dict, List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    # App Settings
    APP_NAME: str = "Fact-Checker & Daily News Digest"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai", "groq", "ollama"
    LLM_MODEL: str = "gemini-3.8-flash"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Search & Tool Settings
    TAVILY_API_KEY: str = ""
    MAX_REACT_ITERATIONS: int = 3
    ENABLE_SAFETY_GUARDRAILS: bool = True
    ENABLE_CLICKBAIT_DETECTION: bool = True
    CREDIBILITY_THRESHOLD: float = 60.0

    # RAG Settings
    RAG_TOP_K: int = 4
    KNOWLEDGE_BASE_PATH: str = str(BASE_DIR / "rag" / "knowledge_base.json")
    VECTOR_CACHE_PATH: str = str(BASE_DIR / "rag" / "embeddings_cache.json")

    # MCP Settings
    MCP_SERVER_NAME: str = "fact-checker-mcp"
    MCP_SERVER_PORT: int = 8080

    # RSS Feeds by Category
    RSS_FEEDS: Dict[str, List[str]] = {
        "World": [
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
            "https://www.aljazeera.com/xml/rss/all.xml"
        ],
        "India": [
            "https://www.thehindu.com/news/national/feeder/default.rss",
            "https://feeds.feedburner.com/ndtvnews-top-stories",
            "https://indianexpress.com/section/india/feed/"
        ],
        "Technology": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://feeds.arstechnica.com/arstechnica/index"
        ],
        "Business": [
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://feeds.bloomberg.com/markets/news.rss"
        ],
        "Science": [
            "https://www.sciencedaily.com/rss/top/science.xml",
            "https://www.nature.com/nature.rss"
        ],
        "Sports": [
            "http://feeds.bbci.co.uk/sport/rss.xml",
            "https://www.espn.com/espn/rss/news"
        ]
    }

    # Trusted Domain Credibility Scores (0 - 100)
    DOMAIN_CREDIBILITY_SCORES: Dict[str, int] = {
        # High Credibility Wire Services & Fact Checkers (90-98)
        "reuters.com": 96,
        "apnews.com": 95,
        "afp.com": 94,
        "snopes.com": 95,
        "politifact.com": 94,
        "factcheck.org": 95,
        "bbc.com": 92,
        "bbc.co.uk": 92,
        "thehindu.com": 90,
        "nature.com": 98,
        "who.int": 97,
        "nasa.gov": 97,
        "cdc.gov": 96,
        "science.org": 98,

        # Reputable News & Tech (80-89)
        "ndtv.com": 85,
        "indianexpress.com": 86,
        "techcrunch.com": 86,
        "theverge.com": 84,
        "arstechnica.com": 88,
        "bloomberg.com": 89,
        "wsj.com": 90,
        "nytimes.com": 88,
        "theguardian.com": 87,
        "aljazeera.com": 83,
        "cnbc.com": 85,

        # Moderate Reliability (60-79)
        "forbes.com": 78,
        "businessinsider.com": 72,
        "medium.com": 60,
        "substack.com": 62,
        "wikipedia.org": 79,

        # Low / Questionable / Tabloid (10-45)
        "dailymail.co.uk": 45,
        "thesun.co.uk": 40,
        "infowars.com": 15,
        "naturalnews.com": 10,
        "theonion.com": 20,  # Satire
        "babylonbee.com": 20  # Satire
    }

settings = Settings()
