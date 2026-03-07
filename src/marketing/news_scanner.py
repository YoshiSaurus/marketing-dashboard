"""News scanner for CS News and fuel marketer industry news.

Scans web sources for convenience store news, fuel distribution news,
and energy industry developments relevant to AI in fuel marketing.
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
            google_api_key: Google Custom Search API key (optional, falls back to scraping)
            google_cx: Google Custom Search Engine ID
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
        """Search for news articles using Google Custom Search API.

        Args:
            query: Search query
            source_name: Name of the news source
            category: Category tag
            max_results: Maximum results to return

        Returns:
            List of NewsArticle objects
        """
        if self.google_api_key and self.google_cx:
            return self._google_custom_search(query, source_name, category, max_results)
        else:
            logger.warning("No Google API key configured, using fallback search")
            return self._fallback_search(query, source_name, category, max_results)

    def _google_custom_search(
        self, query: str, source_name: str, category: str, max_results: int
    ) -> list[NewsArticle]:
        """Use Google Custom Search JSON API.

        Args:
            query: Search query
            source_name: Source name for tagging
            category: Category for the articles
            max_results: Max results

        Returns:
            List of NewsArticle
        """
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
        """Fallback search using Google News RSS-style scraping.

        This is used when no API key is configured. It uses the Google News
        search endpoint to find recent articles.

        Args:
            query: Search query
            source_name: Source name
            category: Category
            max_results: Max results

        Returns:
            List of NewsArticle
        """
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
        """Parse RSS XML content into NewsArticle objects.

        Simple XML parsing without external dependencies.

        Args:
            rss_content: Raw RSS XML string
            source_name: Source name
            category: Category
            max_results: Max articles to extract

        Returns:
            List of NewsArticle
        """
        articles = []

        # Simple XML parsing for RSS items
        items = rss_content.split("<item>")[1:]  # Skip everything before first item

        for item_xml in items[:max_results]:
            title = self._extract_xml_tag(item_xml, "title")
            link = self._extract_xml_tag(item_xml, "link")
            description = self._extract_xml_tag(item_xml, "description")
            pub_date = self._extract_xml_tag(item_xml, "pubDate")

            if title and link:
                # Clean HTML from description
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

        # Try CDATA first
        if cdata_start in xml:
            start = xml.find(cdata_start) + len(cdata_start)
            end = xml.find(cdata_end, start)
            if end > start:
                return xml[start:end]

        # Regular tag
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
        """Get current trending topics in fuel marketing + AI.

        Returns:
            List of trending topic strings
        """
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
