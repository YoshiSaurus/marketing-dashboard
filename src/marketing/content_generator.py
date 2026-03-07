"""Content generator for blog ideas and LinkedIn posts.

Uses Claude/Anthropic API to generate content at the intersection
of news and AI for the fuel marketing and distribution industry.
"""

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .news_scanner import NewsArticle

logger = logging.getLogger(__name__)


@dataclass
class BlogIdea:
    """A generated blog post idea."""
    title: str
    hook: str
    outline: list[str]
    target_audience: str
    ai_angle: str
    source_articles: list[str]
    seo_keywords: list[str]
    estimated_word_count: int = 1200
    status: str = "draft"  # draft, approved, published


@dataclass
class LinkedInPost:
    """A generated LinkedIn post."""
    text: str
    hashtags: list[str]
    call_to_action: str
    source_articles: list[str]
    image_prompt: str = ""
    status: str = "draft"  # draft, approved, published


@dataclass
class ContentSuggestion:
    """A complete content suggestion package."""
    id: str
    created_at: str
    blog_idea: BlogIdea
    linkedin_post: LinkedInPost
    source_articles: list[NewsArticle]
    image_prompt: str = ""
    approval_status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[str] = None
    slack_message_ts: Optional[str] = None


class ContentGenerator:
    """Generates blog ideas and LinkedIn posts from news articles using AI."""

    def __init__(self, anthropic_api_key: str):
        """Initialize the content generator.

        Args:
            anthropic_api_key: Anthropic API key for Claude
        """
        self.api_key = anthropic_api_key

    def generate_content_suggestions(
        self, articles: list[NewsArticle], num_suggestions: int = 3
    ) -> list[ContentSuggestion]:
        """Generate content suggestions from news articles.

        Args:
            articles: List of news articles to draw from
            num_suggestions: Number of suggestions to generate

        Returns:
            List of ContentSuggestion objects
        """
        if not articles:
            logger.warning("No articles provided for content generation")
            return []

        # Group articles by theme for better content generation
        article_summaries = self._prepare_article_summaries(articles)

        suggestions = []
        for i in range(num_suggestions):
            try:
                suggestion = self._generate_single_suggestion(
                    article_summaries, articles, suggestion_index=i
                )
                if suggestion:
                    suggestions.append(suggestion)
            except Exception as e:
                logger.error(f"Failed to generate suggestion {i}: {e}")

        return suggestions

    def _prepare_article_summaries(self, articles: list[NewsArticle]) -> str:
        """Prepare article summaries for the AI prompt.

        Args:
            articles: List of articles

        Returns:
            Formatted string of article summaries
        """
        summaries = []
        for i, article in enumerate(articles[:15], 1):  # Limit to 15 articles
            summaries.append(
                f"{i}. [{article.source}] {article.title}\n"
                f"   URL: {article.url}\n"
                f"   Summary: {article.snippet}\n"
                f"   Category: {article.category}"
            )
        return "\n\n".join(summaries)

    def _generate_single_suggestion(
        self,
        article_summaries: str,
        articles: list[NewsArticle],
        suggestion_index: int,
    ) -> Optional[ContentSuggestion]:
        """Generate a single content suggestion using Claude.

        Args:
            article_summaries: Formatted article summaries
            articles: Original article objects
            suggestion_index: Index for variation

        Returns:
            ContentSuggestion or None
        """
        variation_prompts = [
            "Focus on how AI is transforming fuel pricing and distribution operations.",
            "Focus on how convenience stores and fuel marketers can leverage AI for competitive advantage.",
            "Focus on practical AI use cases that fuel distributors can implement today.",
        ]

        variation = variation_prompts[suggestion_index % len(variation_prompts)]

        prompt = f"""You are a content strategist for Foliox, an AI platform for fuel marketing and distribution.

Based on these recent industry news articles, generate ONE content suggestion that connects current news with AI applications in the fuel marketing and distribution industry.

{variation}

RECENT NEWS ARTICLES:
{article_summaries}

Generate a JSON response with this exact structure:
{{
    "blog": {{
        "title": "Compelling blog title (60-80 chars)",
        "hook": "Opening paragraph hook (2-3 sentences that grab attention)",
        "outline": ["Section 1 title", "Section 2 title", "Section 3 title", "Section 4 title"],
        "target_audience": "Who this blog is for",
        "ai_angle": "How AI connects to the news topic",
        "seo_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
        "source_article_indices": [1, 2]
    }},
    "linkedin": {{
        "text": "LinkedIn post text (150-250 words, conversational, thought-leadership style. Include line breaks for readability. Do NOT include hashtags in the text.)",
        "hashtags": ["#FuelMarketing", "#AIinEnergy", "#tag3", "#tag4", "#tag5"],
        "call_to_action": "What you want readers to do",
        "source_article_indices": [1]
    }},
    "image_prompt": "A detailed prompt for generating an image that represents the intersection of AI and fuel marketing for this specific topic. Be specific about visual elements, style, and mood. The image should be professional and suitable for both blog and LinkedIn."
}}

IMPORTANT: Return ONLY valid JSON, no markdown formatting or code blocks."""

        response_text = self._call_claude(prompt)
        if not response_text:
            return None

        try:
            # Clean response - strip markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return None

        blog_data = data.get("blog", {})
        linkedin_data = data.get("linkedin", {})

        # Map source article indices to URLs
        blog_sources = []
        for idx in blog_data.get("source_article_indices", []):
            if 0 < idx <= len(articles):
                blog_sources.append(articles[idx - 1].url)

        linkedin_sources = []
        for idx in linkedin_data.get("source_article_indices", []):
            if 0 < idx <= len(articles):
                linkedin_sources.append(articles[idx - 1].url)

        # Get the source articles referenced
        source_articles_used = []
        all_indices = set(
            blog_data.get("source_article_indices", [])
            + linkedin_data.get("source_article_indices", [])
        )
        for idx in all_indices:
            if 0 < idx <= len(articles):
                source_articles_used.append(articles[idx - 1])

        blog_idea = BlogIdea(
            title=blog_data.get("title", "Untitled"),
            hook=blog_data.get("hook", ""),
            outline=blog_data.get("outline", []),
            target_audience=blog_data.get("target_audience", "Fuel marketers"),
            ai_angle=blog_data.get("ai_angle", ""),
            source_articles=blog_sources,
            seo_keywords=blog_data.get("seo_keywords", []),
        )

        linkedin_post = LinkedInPost(
            text=linkedin_data.get("text", ""),
            hashtags=linkedin_data.get("hashtags", []),
            call_to_action=linkedin_data.get("call_to_action", ""),
            source_articles=linkedin_sources,
            image_prompt=data.get("image_prompt", ""),
        )

        suggestion_id = f"cs-{datetime.now().strftime('%Y%m%d%H%M%S')}-{suggestion_index}"

        return ContentSuggestion(
            id=suggestion_id,
            created_at=datetime.now().isoformat(),
            blog_idea=blog_idea,
            linkedin_post=linkedin_post,
            source_articles=source_articles_used,
            image_prompt=data.get("image_prompt", ""),
        )

    def generate_full_blog_post(self, blog_idea: BlogIdea) -> str:
        """Generate the full blog post content from an approved blog idea.

        Args:
            blog_idea: Approved BlogIdea

        Returns:
            Full blog post in markdown format
        """
        prompt = f"""Write a complete blog post for Foliox (an AI platform for fuel marketing and distribution).

Title: {blog_idea.title}
Hook: {blog_idea.hook}
Outline: {json.dumps(blog_idea.outline)}
AI Angle: {blog_idea.ai_angle}
Target Audience: {blog_idea.target_audience}
SEO Keywords: {json.dumps(blog_idea.seo_keywords)}

Guidelines:
- Write 1000-1500 words
- Professional but accessible tone
- Include real-world examples where possible
- Reference how AI/automation transforms the specific topic
- Mention Foliox naturally (not salesy) as a solution in the space
- Use markdown formatting with headers, bullet points, etc.
- End with a clear call to action
- Optimize for the provided SEO keywords

Write the complete blog post now:"""

        return self._call_claude(prompt) or ""

    def generate_full_linkedin_post(self, linkedin_post: LinkedInPost) -> str:
        """Polish and finalize a LinkedIn post for publishing.

        Args:
            linkedin_post: Approved LinkedInPost

        Returns:
            Final LinkedIn post text with hashtags
        """
        hashtags_str = " ".join(linkedin_post.hashtags)
        return f"{linkedin_post.text}\n\n{hashtags_str}"

    def _call_claude(self, prompt: str) -> Optional[str]:
        """Call Claude API.

        Args:
            prompt: The prompt to send

        Returns:
            Response text or None on failure
        """
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    return content[0]["text"]
                return None
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"Claude API error: {e.code} - {body[:200]}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"Claude API connection error: {e.reason}")
            return None
