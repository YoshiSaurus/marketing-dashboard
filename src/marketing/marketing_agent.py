"""AI Fuel Marketing Lead Agent - Main orchestrator.

Scans CS News and fuel marketer news, generates blog/LinkedIn content suggestions,
posts to Slack for approval, and publishes approved content.

Architecture:
    News Scan -> Content Generation -> Image Generation -> Slack Approval
    -> Publishing (Website + LinkedIn)
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .news_scanner import NewsScanner, NewsScanResult
from .content_generator import ContentGenerator, ContentSuggestion
from .image_generator import ImageGenerator, GeneratedImage
from .slack_marketing import SlackMarketingClient, ApprovalAction
from .publisher import WebsitePublisher, LinkedInPublisher, PublishResult
from .analytics_db import AnalyticsDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class PendingSuggestion:
    """A suggestion awaiting approval."""
    suggestion: ContentSuggestion
    generated_image: Optional[GeneratedImage] = None
    slack_message_ts: Optional[str] = None
    slack_channel_id: Optional[str] = None


class MarketingAgent:
    """AI Fuel Marketing Lead - scans news, generates content, manages approvals."""

    def __init__(
        self,
        # API Keys
        anthropic_api_key: str,
        gemini_api_key: Optional[str] = None,
        banana_api_key: Optional[str] = None,
        google_search_api_key: Optional[str] = None,
        google_search_cx: Optional[str] = None,
        # Slack config
        slack_webhook_url: str = "",
        slack_bot_token: Optional[str] = None,
        slack_app_token: Optional[str] = None,
        # Website config
        website_api_url: Optional[str] = None,
        website_api_key: Optional[str] = None,
        # LinkedIn config
        linkedin_access_token: Optional[str] = None,
        linkedin_org_id: Optional[str] = None,
        # Agent config
        scan_interval: int = 3600,  # 1 hour default
        num_suggestions: int = 3,
        output_dir: str = "marketing_output",
    ):
        """Initialize the Marketing Agent.

        Args:
            anthropic_api_key: Anthropic API key for Claude content generation
            gemini_api_key: Google Gemini API key for image generation
            banana_api_key: Banana.dev API key for image generation
            google_search_api_key: Google Custom Search API key
            google_search_cx: Google Custom Search Engine ID
            slack_webhook_url: Slack incoming webhook URL
            slack_bot_token: Slack bot token for interactive features
            slack_app_token: Slack app-level token for Socket Mode
            website_api_url: Foliox website API URL
            website_api_key: Website API key
            linkedin_access_token: LinkedIn OAuth2 access token
            linkedin_org_id: LinkedIn organization ID
            scan_interval: Seconds between news scans
            num_suggestions: Number of content suggestions per scan
            output_dir: Directory for generated content and images
        """
        # Initialize components
        self.news_scanner = NewsScanner(
            google_api_key=google_search_api_key,
            google_cx=google_search_cx,
        )

        self.content_generator = ContentGenerator(
            anthropic_api_key=anthropic_api_key,
            knowledge_base_path=os.environ.get("KNOWLEDGE_BASE_PATH"),
        )

        self.image_generator = ImageGenerator(
            gemini_api_key=gemini_api_key,
            banana_api_key=banana_api_key,
            output_dir=os.path.join(output_dir, "images"),
        )

        self.slack = SlackMarketingClient(
            webhook_url=slack_webhook_url,
            bot_token=slack_bot_token,
            app_token=slack_app_token,
        )

        # Publishers (initialized only if configured)
        self.website_publisher = None
        if website_api_url and website_api_key:
            self.website_publisher = WebsitePublisher(
                api_url=website_api_url,
                api_key=website_api_key,
            )

        self.linkedin_publisher = None
        if linkedin_access_token and linkedin_org_id:
            self.linkedin_publisher = LinkedInPublisher(
                access_token=linkedin_access_token,
                organization_id=linkedin_org_id,
            )

        self.scan_interval = scan_interval
        self.num_suggestions = num_suggestions
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Analytics database
        db_path = os.path.join(output_dir, "marketing_analytics.db")
        self.analytics = AnalyticsDB(db_path=db_path)

        # Track pending suggestions
        self._pending: dict[str, PendingSuggestion] = {}
        self._published: list[str] = []

        logger.info("Marketing Agent initialized")

    def run_scan_cycle(self) -> list[ContentSuggestion]:
        """Run a single scan-generate-post cycle.

        1. Scan news sources
        2. Generate content suggestions
        3. Generate images for suggestions
        4. Post suggestions to Slack for approval

        Returns:
            List of generated ContentSuggestion objects
        """
        logger.info("=" * 60)
        logger.info("MARKETING AGENT - Starting scan cycle")
        logger.info("=" * 60)

        # Step 1: Scan news
        logger.info("Step 1: Scanning news sources...")
        scan_result = self.news_scanner.scan_all_sources()
        logger.info(
            f"Found {scan_result.total_found} articles from "
            f"{scan_result.sources_scanned} sources"
        )

        if not scan_result.articles:
            logger.warning("No articles found, skipping content generation")
            self.slack._post_with_webhook({
                "text": (
                    ":newspaper: *Foliox AI Marketing Lead*\n"
                    "Scanned news sources but found no new articles this cycle. "
                    "Will retry next cycle."
                ),
            })
            return []

        # Step 2: Generate content suggestions
        logger.info("Step 2: Generating content suggestions...")
        suggestions = self.content_generator.generate_content_suggestions(
            articles=scan_result.articles,
            num_suggestions=self.num_suggestions,
        )
        logger.info(f"Generated {len(suggestions)} content suggestions")

        if not suggestions:
            logger.warning("No suggestions generated")
            return []

        # Step 3 & 4: Generate images and post to Slack
        for suggestion in suggestions:
            # Generate image
            logger.info(f"Step 3: Generating image for suggestion {suggestion.id}...")
            generated_image = None
            if suggestion.image_prompt:
                generated_image = self.image_generator.generate_image(
                    prompt=suggestion.image_prompt,
                    style="professional",
                    suggestion_id=suggestion.id,
                )
                if generated_image:
                    logger.info(f"Image generated: {generated_image.file_path}")

            # Post to Slack
            logger.info(f"Step 4: Posting suggestion {suggestion.id} to Slack...")
            image_path = generated_image.file_path if generated_image else None
            message_ts = self.slack.post_content_suggestion(
                suggestion=suggestion,
                image_path=image_path,
            )

            # Track the pending suggestion
            self._pending[suggestion.id] = PendingSuggestion(
                suggestion=suggestion,
                generated_image=generated_image,
                slack_message_ts=message_ts,
            )

            logger.info(f"Suggestion {suggestion.id} posted to Slack")

        # Save suggestions to disk and database
        self._save_suggestions(suggestions)
        for suggestion in suggestions:
            try:
                self.analytics.record_suggestion(suggestion)
            except Exception as e:
                logger.error(f"Failed to record suggestion in analytics: {e}")

        self.analytics.record_scan_cycle(
            articles_found=scan_result.total_found,
            suggestions_generated=len(suggestions),
            sources_scanned=scan_result.sources_scanned,
        )

        logger.info(f"Scan cycle complete. {len(suggestions)} suggestions posted to Slack.")
        return suggestions

    def handle_approval(self, approval: ApprovalAction) -> None:
        """Handle an approval action from Slack.

        Args:
            approval: The approval action from Slack
        """
        suggestion_id = approval.suggestion_id
        pending = self._pending.get(suggestion_id)

        if not pending:
            logger.warning(f"Suggestion {suggestion_id} not found in pending")
            return

        logger.info(
            f"Handling approval for {suggestion_id}: "
            f"{approval.action} by {approval.user_name}"
        )

        # Update approval status
        pending.suggestion.approval_status = (
            "approved" if approval.action != "reject" else "rejected"
        )
        pending.suggestion.approved_by = approval.user_name

        # Record in analytics
        try:
            self.analytics.record_approval(suggestion_id, approval.action, approval.user_name)
        except Exception as e:
            logger.error(f"Failed to record approval in analytics: {e}")

        # Post update to Slack
        self.slack.post_approval_update(
            suggestion_id=suggestion_id,
            action=approval.action,
            user_name=approval.user_name,
            response_url=approval.response_url,
        )

        if approval.action == "reject":
            logger.info(f"Suggestion {suggestion_id} rejected")
            return

        # Check for images in Slack thread replies
        thread_images = []
        if pending.slack_message_ts and pending.slack_channel_id:
            image_urls = self.slack.get_thread_images(
                channel_id=pending.slack_channel_id,
                message_ts=pending.slack_message_ts,
            )
            for url in image_urls:
                img = self.image_generator.download_slack_image(
                    image_url=url,
                    slack_bot_token=self.slack.bot_token or "",
                    suggestion_id=suggestion_id,
                )
                if img:
                    thread_images.append(img)

        # Determine which image to use (thread images take priority)
        image_path = None
        if thread_images:
            image_path = thread_images[0].file_path
        elif pending.generated_image:
            image_path = pending.generated_image.file_path

        # Publish based on action (LinkedIn is manual-only now)
        blog_url = None

        if approval.action in ("approve_all", "approve_blog"):
            blog_url = self._publish_blog(pending.suggestion, image_path)

        # Post publishing status to Slack
        self.slack.post_publishing_status(
            suggestion_id=suggestion_id,
            blog_url=blog_url,
            linkedin_url=None,
        )

        self._published.append(suggestion_id)
        logger.info(f"Suggestion {suggestion_id} publishing complete")

    def _publish_blog(
        self, suggestion: ContentSuggestion, image_path: Optional[str]
    ) -> Optional[str]:
        """Generate and publish a full blog post.

        Args:
            suggestion: Approved content suggestion
            image_path: Path to featured image

        Returns:
            Published blog URL or None
        """
        if not self.website_publisher:
            logger.warning("Website publisher not configured, skipping blog publish")
            return None

        logger.info("Generating full blog post...")
        blog_content = self.content_generator.generate_full_blog_post(
            suggestion.blog_idea
        )

        if not blog_content:
            logger.error("Failed to generate blog post content")
            return None

        logger.info("Publishing blog post to website...")
        result = self.website_publisher.publish_blog_post(
            title=suggestion.blog_idea.title,
            content=blog_content,
            featured_image_path=image_path,
            tags=suggestion.blog_idea.seo_keywords,
            status="publish",
        )

        if result.success:
            logger.info(f"Blog published: {result.url}")
            try:
                self.analytics.record_published_post(
                    suggestion_id=suggestion.id,
                    platform="website",
                    post_type="blog",
                    content_category=getattr(suggestion, 'content_category', 'general'),
                    title=suggestion.blog_idea.title,
                    content_preview=suggestion.blog_idea.hook,
                    url=result.url,
                    post_id=result.post_id,
                    image_used=image_path is not None,
                )
            except Exception as e:
                logger.error(f"Failed to record published post in analytics: {e}")
            return result.url
        else:
            logger.error(f"Blog publish failed: {result.error}")
            return None

    def _publish_linkedin(
        self,
        suggestion: ContentSuggestion,
        image_path: Optional[str],
        blog_url: Optional[str],
    ) -> Optional[str]:
        """Publish a LinkedIn post.

        Args:
            suggestion: Approved content suggestion
            image_path: Path to image
            blog_url: URL of blog post to link (if published)

        Returns:
            Published LinkedIn URL or None
        """
        if not self.linkedin_publisher:
            logger.warning("LinkedIn publisher not configured, skipping LinkedIn publish")
            return None

        # Generate final LinkedIn text
        post_text = self.content_generator.generate_full_linkedin_post(
            suggestion.linkedin_post
        )

        logger.info("Publishing LinkedIn post...")
        result = self.linkedin_publisher.publish_post(
            text=post_text,
            image_path=image_path,
            article_url=blog_url,
            article_title=suggestion.blog_idea.title if blog_url else None,
        )

        if result.success:
            logger.info(f"LinkedIn post published: {result.url}")
            return result.url
        else:
            logger.error(f"LinkedIn publish failed: {result.error}")
            return None

    def _save_suggestions(self, suggestions: list[ContentSuggestion]) -> None:
        """Save suggestions to disk for persistence.

        Args:
            suggestions: List of suggestions to save
        """
        suggestions_dir = os.path.join(self.output_dir, "suggestions")
        os.makedirs(suggestions_dir, exist_ok=True)

        for suggestion in suggestions:
            filepath = os.path.join(suggestions_dir, f"{suggestion.id}.json")
            twitter_data = None
            if suggestion.twitter_post:
                twitter_data = {
                    "text": suggestion.twitter_post.text,
                    "hashtags": suggestion.twitter_post.hashtags,
                    "post_type": suggestion.twitter_post.post_type,
                    "source_articles": suggestion.twitter_post.source_articles,
                }

            data = {
                "id": suggestion.id,
                "created_at": suggestion.created_at,
                "content_category": suggestion.content_category,
                "blog_idea": {
                    "title": suggestion.blog_idea.title,
                    "hook": suggestion.blog_idea.hook,
                    "outline": suggestion.blog_idea.outline,
                    "target_audience": suggestion.blog_idea.target_audience,
                    "ai_angle": suggestion.blog_idea.ai_angle,
                    "source_articles": suggestion.blog_idea.source_articles,
                    "seo_keywords": suggestion.blog_idea.seo_keywords,
                },
                "linkedin_post": {
                    "text": suggestion.linkedin_post.text,
                    "hashtags": suggestion.linkedin_post.hashtags,
                    "call_to_action": suggestion.linkedin_post.call_to_action,
                    "source_articles": suggestion.linkedin_post.source_articles,
                },
                "twitter_post": twitter_data,
                "image_prompt": suggestion.image_prompt,
                "source_articles": [
                    {"title": a.title, "url": a.url, "source": a.source}
                    for a in suggestion.source_articles
                ],
                "approval_status": suggestion.approval_status,
            }

            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

        logger.info(f"Saved {len(suggestions)} suggestions to {suggestions_dir}")

    def run(self) -> None:
        """Run the marketing agent continuously.

        Scans news and generates content at the configured interval.
        """
        logger.info("=" * 60)
        logger.info("FOLIOX AI MARKETING LEAD")
        logger.info("=" * 60)
        logger.info(f"  Scan interval: {self.scan_interval} seconds")
        logger.info(f"  Suggestions per cycle: {self.num_suggestions}")
        logger.info(f"  Output directory: {self.output_dir}")
        logger.info(f"  Website publisher: {'configured' if self.website_publisher else 'not configured'}")
        logger.info(f"  LinkedIn publisher: {'configured' if self.linkedin_publisher else 'not configured'}")
        logger.info("=" * 60)
        logger.info("Agent is running. Press Ctrl+C to stop.")
        logger.info("")

        try:
            while True:
                try:
                    self.run_scan_cycle()
                except Exception as e:
                    logger.error(f"Error in scan cycle: {e}", exc_info=True)

                logger.info(f"Next scan in {self.scan_interval} seconds...")
                time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            logger.info("Marketing Agent stopped by user")
