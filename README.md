# 📰 Fact-Checker & Daily News Digest

**Domain:** News / Media  
**Type:** College Project  
**Tech Stack:** Python, Flask, SQLite, NLP, HTML/CSS/JavaScript

---

## 📌 Project Overview

**Fact-Checker & Daily News Digest** is a web application that gathers the latest news from trusted sources, summarizes it into a short daily digest, and lets users check whether a news claim is true, false, or misleading.

Fake news spreads fast on social media, and most people don't have time to read many full articles. This project solves both problems:

1. **Daily News Digest:** collects news every day and gives short summaries grouped by category.
2. **Fact-Checker:** checks a claim or headline against trusted news sources and fact-check databases, then gives a verdict with a credibility score.

---

## 🎯 Objectives

- Collect news automatically from trusted RSS feeds and news APIs
- Summarize long articles into 2–3 key sentences using NLP
- Build a daily digest grouped by category (World, India, Tech, Business, Science, Sports)
- Verify user-submitted claims and show a verdict with evidence
- Detect sensational or clickbait language in headlines
- Keep a history of fact-checks and past digests

---

## ✨ Features

| Feature | Description |
|---|---|
| 📥 News Aggregation | Fetches news from RSS feeds (BBC, The Hindu, NDTV, Al Jazeera, TechCrunch) |
| ✂️ Auto Summarization | Extractive summarization using word-frequency sentence scoring |
| 🗂️ Category-wise Digest | Daily digest arranged by news category |
| ✅ Fact-Checker | Verifies claims using Google Fact Check API + news cross-referencing |
| 📊 Credibility Score | 0–100 score based on source reliability and evidence match |
| 🚩 Clickbait Detection | Flags ALL CAPS, excessive "!!!", and sensational words |
| 🕘 History | Stores past fact-checks and digests in SQLite |
| 📄 Export | Download the daily digest as HTML / Markdown |
| 🔌 REST API | JSON endpoints for news and fact-check results |

---

## 🧠 How It Works

### 1. Daily News Digest
```
RSS Feeds / News API  →  Fetch Articles  →  Clean Text  →  Summarize (NLP)
        →  Group by Category  →  Store in Database  →  Generate Daily Digest
```

### 2. Fact-Checker
```
User enters claim  →  Extract keywords
        →  Search known fact-check database (Google Fact Check API)
        →  Cross-check with trusted news articles
        →  Weight evidence by source credibility
        →  Check for clickbait / sensational language
        →  Final Verdict + Score + Evidence links
```

### Verdict Levels

| Score | Verdict |
|---|---|
| 80 – 100 | ✅ TRUE |
| 60 – 79 | 🟢 LIKELY TRUE |
| 40 – 59 | 🟡 UNVERIFIED |
| 20 – 39 | 🟠 MISLEADING |
| 0 – 19 | ❌ FALSE |

---

## 📁 Project Folder Structure

```
Fact-Checker & Daily News Digest/
│
├── backend/                              # Server-side logic
│   ├── api/                              # Flask REST API
│   │   ├── routes/                       # URL routes
│   │   ├── controllers/                  # Request handling logic
│   │   ├── middleware/                   # Auth, logging, error handling
│   │   ├── validators/                   # Input validation
│   │   └── schemas/                      # Request/response formats
│   │
│   ├── news_fetcher/                     # News collection module
│   │   ├── rss_feeds/                    # RSS feed readers (BBC, The Hindu, NDTV)
│   │   ├── news_api/                     # NewsAPI integration
│   │   ├── web_scrapers/                 # Website scrapers
│   │   ├── parsers/                      # Article parsers
│   │   └── cleaners/                     # HTML / text cleaning
│   │
│   ├── summarizer/                       # NLP summarization module
│   │   ├── preprocessing/                # Tokenizing, stopword removal
│   │   ├── extractive/                   # Frequency-based summarizer
│   │   ├── abstractive/                  # Transformer-based summarizer
│   │   └── keyword_extraction/           # Key topic extraction
│   │
│   ├── fact_checker/                     # Fact verification module
│   │   ├── claim_extraction/             # Extract claims from text
│   │   ├── google_factcheck/             # Google Fact Check API
│   │   ├── cross_reference/              # Match claims with trusted news
│   │   ├── source_credibility/           # Source reliability scoring
│   │   ├── clickbait_detection/          # Sensational headline detection
│   │   ├── sentiment_analysis/           # Tone / bias analysis
│   │   └── verdict_engine/               # Final verdict & score
│   │
│   ├── digest_generator/                 # Daily digest module
│   │   ├── builders/                     # Build digest by category
│   │   ├── formatters/                   # Layout & formatting
│   │   └── exporters/
│   │       ├── html/                     # HTML export
│   │       ├── markdown/                 # Markdown export
│   │       └── pdf/                      # PDF export
│   │
│   ├── database/                         # SQLite database layer
│   │   ├── models/                       # Tables: articles, fact_checks
│   │   ├── migrations/                   # Schema changes
│   │   ├── queries/                      # Database queries
│   │   └── seeds/                        # Initial sample data
│   │
│   ├── services/                         # Background services
│   │   ├── email/                        # Email digest delivery
│   │   ├── notifications/                # Alerts & push notifications
│   │   ├── scheduler/                    # Daily auto-run jobs
│   │   └── cache/                        # Caching layer
│   │
│   ├── utils/
│   │   ├── text_processing/              # Text helper functions
│   │   ├── logging/                      # Logger setup
│   │   └── helpers/                      # Common helpers
│   │
│   └── config/                           # Backend settings
│
├── frontend/                             # User interface
│   ├── templates/
│   │   ├── layouts/                      # Base page layout
│   │   ├── components/
│   │   │   ├── navbar/
│   │   │   ├── footer/
│   │   │   ├── news_card/
│   │   │   └── verdict_card/
│   │   ├── pages/
│   │   │   ├── home/                     # Latest news
│   │   │   ├── digest/                   # Daily digest
│   │   │   ├── factcheck/                # Fact-check form & result
│   │   │   ├── history/                  # Past fact-checks
│   │   │   └── about/
│   │   └── errors/                       # 404 / 500 pages
│   │
│   └── static/
│       ├── css/  (base/, components/, pages/, themes/)
│       ├── js/   (modules/, pages/, vendor/)
│       ├── images/ (logos/, icons/, banners/, source_logos/)
│       └── fonts/
│
├── data/
│   ├── raw/                              # Raw fetched data
│   │   ├── rss_feeds/
│   │   ├── news_api/
│   │   └── scraped/
│   ├── processed/                        # Processed data
│   │   ├── cleaned/
│   │   ├── summarized/
│   │   └── categorized/
│   ├── known_claims/                     # Verified claims database
│   │   ├── true_claims/
│   │   ├── false_claims/
│   │   └── misleading_claims/
│   ├── datasets/                         # ML datasets
│   │   ├── fake_news_dataset/
│   │   ├── liar_dataset/
│   │   ├── training/
│   │   ├── testing/
│   │   └── validation/
│   └── sources/
│       └── credibility_scores/           # Trusted source ratings
│
├── digests/                              # Generated digests
│   ├── daily/
│   │   └── 2026/
│   │       ├── 09-September/
│   │       └── 10-October/
│   ├── weekly/
│   └── archive/
│
├── models/                               # Saved ML / NLP models
│   ├── summarizer/
│   ├── fake_news_classifier/
│   │   └── checkpoints/
│   ├── vectorizers/
│   └── embeddings/
│
├── notebooks/                            # Jupyter notebooks
│   ├── data_exploration/
│   ├── model_training/
│   └── experiments/
│
├── scripts/                              # Utility scripts
│   ├── scheduler/                        # Run digest daily
│   ├── setup/                            # Project setup
│   ├── data_collection/
│   └── maintenance/
│
├── tests/                                # Testing
│   ├── unit/
│   │   ├── news_fetcher/
│   │   ├── summarizer/
│   │   ├── fact_checker/
│   │   ├── digest_generator/
│   │   └── database/
│   ├── integration/
│   │   ├── api/
│   │   └── pipeline/
│   └── fixtures/
│       ├── sample_news/
│       └── sample_claims/
│
├── docs/                                 # Documentation
│   ├── report/
│   │   └── chapters/                     # Project report chapters
│   ├── diagrams/
│   │   ├── architecture/
│   │   ├── data_flow/                    # DFD diagrams
│   │   ├── er_diagram/
│   │   └── uml/
│   │       ├── use_case/
│   │       ├── sequence/
│   │       ├── class/
│   │       └── activity/
│   ├── screenshots/
│   │   ├── home/
│   │   ├── digest/
│   │   ├── factcheck/
│   │   └── history/
│   ├── presentation/                     # PPT slides
│   └── references/                       # Research papers
│
├── logs/                                 # Application logs
│   ├── app/
│   ├── scheduler/
│   └── errors/
│
├── deployment/                           # Deployment files
│   ├── docker/
│   ├── nginx/
│   └── cloud/
│
├── config/                               # Environment configs
│   ├── development/
│   ├── production/
│   └── testing/
│
└── README.md                             # Project documentation
```

---

## 🛠️ Technologies Used

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Web Framework | Flask |
| Frontend | HTML5, CSS3, JavaScript |
| Database | SQLite |
| News Source | RSS Feeds (feedparser), NewsAPI |
| Fact-Check Source | Google Fact Check Tools API |
| NLP | Word-frequency summarization, keyword extraction, NLTK |
| Scheduler | Windows Task Scheduler / cron |
| Testing | pytest |

---

## ⚙️ Installation & Setup

```bash
# 1. Go to the project folder
cd "Fact-Checker & Daily News Digest"

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux / Mac

# 3. Install dependencies
pip install flask feedparser requests python-dotenv nltk pytest

# 4. (Optional) Add API key in a .env file
GOOGLE_FACTCHECK_API_KEY=your_api_key_here

# 5. Run the application
python app.py
```

Open in browser: **http://127.0.0.1:5000**

---

## 🖥️ Application Pages

| Page | URL | Description |
|---|---|---|
| Home | `/` | Latest news by category |
| Daily Digest | `/digest` | Today's summarized news digest |
| Fact-Check | `/factcheck` | Enter a claim and get a verdict |
| History | `/history` | Past fact-check results |

### REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/news?category=World` | Get latest news (JSON) |
| GET | `/api/digest` | Get today's digest (JSON) |
| POST | `/api/factcheck` | Check a claim → `{ "claim": "..." }` |

---

## 🧪 Example

**Input claim:**
> "Drinking hot water cures COVID-19"

**Output:**
```
Verdict      : ❌ FALSE
Score        : 8 / 100
Explanation  : Matched a known false claim reviewed by fact-checkers (WHO, PIB Fact Check).
Evidence     : 3 trusted sources contradict this claim.
Clickbait    : No
```

---

## 🗄️ Database Design

**Table: `articles`**
| Column | Type |
|---|---|
| id | INTEGER (PK) |
| title | TEXT |
| link | TEXT (UNIQUE) |
| summary | TEXT |
| source | TEXT |
| category | TEXT |
| published | TEXT |

**Table: `fact_checks`**
| Column | Type |
|---|---|
| id | INTEGER (PK) |
| claim | TEXT |
| verdict | TEXT |
| score | INTEGER |
| explanation | TEXT |
| checked_at | TEXT |

---

## 🚀 Future Enhancements

- Deep-learning fake news classifier (BERT / LSTM)
- Multi-language news support (Tamil, Hindi)
- Email / WhatsApp / Telegram daily digest delivery
- Browser extension to fact-check any webpage
- Image and video fake detection
- User login with personalized news categories

---

## 📚 Conclusion

This project gives users one place to **read verified news quickly** and **check suspicious claims**. It combines news aggregation, NLP summarization, and fact-checking to help reduce misinformation and save the reader's time.

---

## 👨‍💻 Developed By

**Name:** _Your Name_  
**Register No:** _Your Register Number_  
**Department:** _Your Department_  
**College:** _Your College Name_  
**Guide:** _Guide Name_  
**Academic Year:** 2026 – 2027
