"""News scanner for CS News and fuel marketer industry news.

Scans web sources for convenience store news, fuel distribution news,
and energy industry developments relevant to AI in fuel marketing.

Uses Gemini API with Google Search grounding (no CX required) as the
primary search method, with Google News RSS as fallback.
"""

import json
import logging
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# News sources for fuel marketing and distribution industry
NEWS_SOURCES = [
    {
        "name": "CSP Daily News",
        "search_query": "convenience store fuel marketing technology",
        "category": "cs_news",
    },
    {
        "name": "NACS",
        "search_query": "NACS convenience fuel retail innovation",
        "category": "cs_news",
    },
    {
        "name": "Fuel Marketer News",
        "search_query": "fuel marketer news distribution wholesale",
        "category": "fuel_marketer",
    },
    {
        "name": "Oil & Energy Magazine",
        "search_query": "fuel distribution technology automation",
        "category": "fuel_marketer",
    },
    {
        "name": "Convenience Store Decisions",
        "search_query": "convenience store decisions fuel pricing",
        "category": "cs_news",
    },
    {
        "name": "Fuels Market News",
        "search_query": "fuels market news petroleum distribution AI",
        "category": "fuel_marketer",
    },
    {
        "name": "Energy AI",
        "search_query": "artificial intelligence fuel energy distribution automation",
        "category": "ai_energy",
    },
]

# AI + fuel marketing intersection topics
AI_FUEL_TOPICS = [
    "AI fuel pricing optimization",
    "machine learning fuel distribution",
    "artificial intelligence convenience store operations",
    "predictive analytics fuel demand forecasting",
    "AI-powered fleet management fuel delivery",
    "automated fuel supply chain",
    "smart fuel inventory management",
    "AI rack pricing petroleum wholesale",
    "digital transformation fuel marketing",
    "generative AI energy industry",
]


@dataclass
class NewsArticle:
    """A scraped news article."""
    title: str
    url: str
    snippet: str
    source: str
    category: str
    published_date: Optional[str] = None
    relevance_score: float = 0.0
    ai_angle: str = ""


@dataclass
class NewsScanResult:
    """Result of a news scanning session."""
    articles: list[NewsArticle] = field(default_factory=list)
    scan_time: str = field(default_factory=lambda: datetime.now().isoformat())
    sources_scanned: int = 0
    total_found: int = 0


class NewsScanner:
    """Scans web for CS News and fuel marketer news relevant to AI in fuel marketing."""

    def __init__(self, google_api_key: Optional[str] = None, google_cx: Optional[str] = None):
        """Initialize the news scanner.

        Args:
            google_api_key: Gemini / Google API key (used for Gemini grounded search)
            google_cx: Google Custom Search Engine ID (optional, used if provided)
        """
        self.google_api_key = google_api_key
        self.google_cx = google_cx

    def scan_all_sources(self, max_articles_per_source: int = 5) -> NewsScanResult:
        """Scan all configured news sources.

        Args:
            max_articles_per_source: Max articles to fetch per source

        Returns:
            NewsScanResult with all found articles
        """
        result = NewsScanResult()

        # Scan industry news sources
        for source in NEWS_SOURCES:
            try:
                articles = self._search_news(
                    query=source["search_query"],
                    source_name=source["name"],
                    category=source["category"],
                    max_results=max_articles_per_source,
                )
                result.articles.extend(articles)
                result.sources_scanned += 1
                logger.info(f"Scanned {source['name']}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"Failed to scan {source['name']}: {e}")

        # Scan AI + fuel intersection topics
        for topic in AI_FUEL_TOPICS[:3]:  # Limit to avoid rate limits
            try:
                articles = self._search_news(
                    query=topic,
                    source_name="AI+Fuel Search",
                    category="ai_fuel_intersection",
                    max_results=3,
                )
                result.articles.extend(articles)
                result.sources_scanned += 1
            except Exception as e:
                logger.error(f"Failed to search topic '{topic}': {e}")

        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in result.articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        result.articles = unique_articles
        result.total_found = len(unique_articles)

        logger.info(f"News scan complete: {result.total_found} unique articles from {result.sources_scanned} sources")
        return result

    def _search_news(
        self, query: str, source_name: str, category: str, max_results: int = 5
    ) -> list[NewsArticle]:
        """Search for news articles.

        Tries Gemini grounded search first (no CX needed), then Custom Search
        if CX is available, then falls back to Google News RSS.
        """
        if self.google_api_key:
            articles = self._gemini_grounded_search(query, source_name, category, max_results)
            if articles:
                return articles
            # Fall back to Custom Search if CX is available
            if self.google_cx:
                articles = self._google_custom_search(query, source_name, category, max_results)
                if articles:
                    return articles

        logger.info("Using RSS fallback search")
        return self._fallback_search(query, source_name, category, max_results)

    def _gemini_grounded_search(
        self, query: str, source_name: str, category: str, max_results: int
    ) -> list[NewsArticle]:
        """Use Gemini API with Google Search grounding to find news articles.

        This uses Gemini's built-in Google Search tool — no CX required.
        """
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                f"Find {max_results} recent news articles about: {query}\n\n"
                                "For each article, provide a JSON array with objects containing:\n"
                                '- "title": article headline\n'
                                '- "url": full article URL\n'
                                '- "snippet": 1-2 sentence summary\n'
                                '- "published_date": publication date if available\n\n'
                                "Return ONLY a valid JSON array, no other text."
                            )
                        }
                    ],
                    "role": "user",
                }
            ],
            "tools": [{"google_search": {}}],
            "generationConfig": {
                "temperature": 0.1,
            },
        }

        data = json.dumps(payload).encode("utf-8")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={self.google_api_key}"
        )

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Gemini grounded search failed: {e}")
            return []

        # Extract text response and parse JSON
        candidates = result.get("candidates", [])
        if not candidates:
            logger.warning("No candidates in Gemini search response")
            return []

        parts = candidates[0].get("content", {}).get("parts", [])
        text_response = ""
        for part in parts:
            if "text" in part:
                text_response += part["text"]

        if not text_response:
            # Try to extract articles from grounding metadata instead
            grounding = candidates[0].get("groundingMetadata", {})
            return self._parse_grounding_metadata(grounding, source_name, category, max_results)

        # Parse the JSON response
        try:
            cleaned = text_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            articles_data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini search response as JSON, trying grounding metadata")
            grounding = candidates[0].get("groundingMetadata", {})
            return self._parse_grounding_metadata(grounding, source_name, category, max_results)

        articles = []
        if isinstance(articles_data, list):
            for item in articles_data[:max_results]:
                if isinstance(item, dict) and item.get("title") and item.get("url"):
                    articles.append(NewsArticle(
                        title=item["title"],
                        url=item["url"],
                        snippet=item.get("snippet", ""),
                        source=source_name,
                        category=category,
                        published_date=item.get("published_date"),
                    ))

        logger.info(f"Gemini grounded search found {len(articles)} articles for '{query}'")
        return articles

    def _parse_grounding_metadata(
        self, grounding: dict, source_name: str, category: str, max_results: int
    ) -> list[NewsArticle]:
        """Extract articles from Gemini grounding metadata (search results)."""
        articles = []
        chunks = grounding.get("groundingChunks", [])
        for chunk in chunks[:max_results]:
            web = chunk.get("web", {})
            if web.get("uri") and web.get("title"):
                articles.append(NewsArticle(
                    title=web["title"],
                    url=web["uri"],
                    snippet="",
                    source=source_name,
                    category=category,
                ))

        support = grounding.get("groundingSupports", [])
        for s in support:
            segment = s.get("segment", {})
            snippet = segment.get("text", "")
            indices = s.get("groundingChunkIndices", [])
            for idx in indices:
                if idx < len(articles) and not articles[idx].snippet:
                    articles[idx].snippet = snippet[:300]

        return articles

    def _google_custom_search(
        self, query: str, source_name: str, category: str, max_results: int
    ) -> list[NewsArticle]:
        """Use Google Custom Search JSON API."""
        params = urllib.parse.urlencode({
            "key": self.google_api_key,
            "cx": self.google_cx,
            "q": query,
            "num": min(max_results, 10),
            "dateRestrict": "d7",  # Last 7 days
            "sort": "date",
        })

        url = f"https://www.googleapis.com/customsearch/v1?{params}"

        req = urllib.request.Request(url, headers={"Accept": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Google Custom Search failed: {e}")
            return []

        articles = []
        for item in data.get("items", []):
            article = NewsArticle(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source=source_name,
                category=category,
                published_date=item.get("pagemap", {}).get("metatags", [{}])[0].get(
                    "article:published_time", ""
                ),
            )
            articles.append(article)

        return articles

    def _fallback_search(
        self, query: str, source_name: str, category: str, max_results: int
    ) -> list[NewsArticle]:
        """Fallback search using Google News RSS."""
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; FolioxBot/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                rss_content = response.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Fallback search failed for '{query}': {e}")
            return []

        return self._parse_rss(rss_content, source_name, category, max_results)

    def _parse_rss(
        self, rss_content: str, source_name: str, category: str, max_results: int
    ) -> list[NewsArticle]:
        """Parse RSS XML content into NewsArticle objects."""
        articles = []

        items = rss_content.split("<item>")[1:]

        for item_xml in items[:max_results]:
            title = self._extract_xml_tag(item_xml, "title")
            link = self._extract_xml_tag(item_xml, "link")
            description = self._extract_xml_tag(item_xml, "description")
            pub_date = self._extract_xml_tag(item_xml, "pubDate")

            if title and link:
                description = self._strip_html(description or "")

                article = NewsArticle(
                    title=self._strip_html(title),
                    url=link.strip(),
                    snippet=description[:300],
                    source=source_name,
                    category=category,
                    published_date=pub_date,
                )
                articles.append(article)

        return articles

    @staticmethod
    def _extract_xml_tag(xml: str, tag: str) -> Optional[str]:
        """Extract content from an XML tag."""
        start_tag = f"<{tag}>"
        end_tag = f"</{tag}>"
        cdata_start = f"<{tag}><![CDATA["
        cdata_end = f"]]></{tag}>"

        if cdata_start in xml:
            start = xml.find(cdata_start) + len(cdata_start)
            end = xml.find(cdata_end, start)
            if end > start:
                return xml[start:end]

        start = xml.find(start_tag)
        if start == -1:
            return None
        start += len(start_tag)
        end = xml.find(end_tag, start)
        if end == -1:
            return None
        return xml[start:end].strip()

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        import re
        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        clean = clean.replace("&quot;", '"').replace("&#39;", "'")
        return clean.strip()

    def get_trending_topics(self) -> list[str]:
        """Get current trending topics in fuel marketing + AI."""
        return [
            "AI-powered fuel rack pricing optimization",
            "Machine learning for fuel demand forecasting",
            "Automated fuel supply chain management",
            "Digital transformation in convenience stores",
            "Predictive analytics for fuel inventory",
            "AI chatbots for fuel distribution customer service",
            "Computer vision for fuel delivery verification",
            "Smart pricing algorithms for fuel marketers",
            "Generative AI for fuel marketing content",
            "IoT and AI in fuel tank monitoring",
        ]
