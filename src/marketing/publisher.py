"""Publisher for posting approved content to website and LinkedIn.

Handles publishing blog posts to the Foliox website and LinkedIn posts
to the Foliox company LinkedIn page.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """Result of a publish operation."""
    platform: str  # "website", "linkedin"
    success: bool
    url: Optional[str] = None
    post_id: Optional[str] = None
    error: Optional[str] = None
    published_at: str = ""


class WebsitePublisher:
    """Publishes blog posts to the Foliox website via API."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
    ):
        """Initialize the website publisher.

        Args:
            api_url: Base URL of the website API (e.g., WordPress REST API)
            api_key: API key or auth token for the website
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    def publish_blog_post(
        self,
        title: str,
        content: str,
        featured_image_path: Optional[str] = None,
        categories: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        status: str = "draft",
    ) -> PublishResult:
        """Publish a blog post to the website.

        Supports WordPress REST API format. Can be adapted for other CMS platforms.

        Args:
            title: Post title
            content: Post content in HTML or markdown
            featured_image_path: Path to featured image
            categories: List of category names
            tags: List of tag names
            status: Post status ("draft", "publish", "pending")

        Returns:
            PublishResult
        """
        # Upload featured image first if provided
        featured_media_id = None
        if featured_image_path and os.path.exists(featured_image_path):
            featured_media_id = self._upload_media(featured_image_path)

        # Create the post
        post_data = {
            "title": title,
            "content": content,
            "status": status,
            "categories": categories or ["AI", "Fuel Marketing"],
            "tags": tags or [],
        }

        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        data = json.dumps(post_data).encode("utf-8")

        req = urllib.request.Request(
            f"{self.api_url}/wp-json/wp/v2/posts",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            post_url = result.get("link", "")
            post_id = str(result.get("id", ""))

            logger.info(f"Blog post published: {post_url}")
            return PublishResult(
                platform="website",
                success=True,
                url=post_url,
                post_id=post_id,
                published_at=datetime.now().isoformat(),
            )

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"Website publish failed: {e.code} - {body[:200]}")
            return PublishResult(
                platform="website",
                success=False,
                error=f"HTTP {e.code}: {body[:200]}",
            )
        except urllib.error.URLError as e:
            logger.error(f"Website publish connection error: {e.reason}")
            return PublishResult(
                platform="website",
                success=False,
                error=str(e.reason),
            )

    def _upload_media(self, image_path: str) -> Optional[int]:
        """Upload an image to the website media library.

        Args:
            image_path: Path to the image file

        Returns:
            Media ID or None
        """
        import mimetypes

        content_type = mimetypes.guess_type(image_path)[0] or "image/png"
        filename = os.path.basename(image_path)

        with open(image_path, "rb") as f:
            file_data = f.read()

        req = urllib.request.Request(
            f"{self.api_url}/wp-json/wp/v2/media",
            data=file_data,
            headers={
                "Content-Type": content_type,
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                media_id = result.get("id")
                logger.info(f"Media uploaded: ID {media_id}")
                return media_id
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Media upload failed: {e}")
            return None


class LinkedInPublisher:
    """Publishes posts to the Foliox LinkedIn company page."""

    def __init__(
        self,
        access_token: str,
        organization_id: str,
    ):
        """Initialize the LinkedIn publisher.

        Args:
            access_token: LinkedIn OAuth2 access token
            organization_id: LinkedIn organization/company page ID
        """
        self.access_token = access_token
        self.organization_id = organization_id

    def publish_post(
        self,
        text: str,
        image_path: Optional[str] = None,
        article_url: Optional[str] = None,
        article_title: Optional[str] = None,
    ) -> PublishResult:
        """Publish a post to the LinkedIn company page.

        Args:
            text: Post text content
            image_path: Optional path to image to attach
            article_url: Optional article URL to share
            article_title: Optional article title for link preview

        Returns:
            PublishResult
        """
        # Upload image if provided
        image_urn = None
        if image_path and os.path.exists(image_path):
            image_urn = self._upload_image(image_path)

        # Build the post payload
        author = f"urn:li:organization:{self.organization_id}"

        post_data = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        share_content = post_data["specificContent"]["com.linkedin.ugc.ShareContent"]

        # Add image if uploaded
        if image_urn:
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "media": image_urn,
                }
            ]
        # Or add article link
        elif article_url:
            share_content["shareMediaCategory"] = "ARTICLE"
            share_content["media"] = [
                {
                    "status": "READY",
                    "originalUrl": article_url,
                    "title": {"text": article_title or ""},
                }
            ]

        data = json.dumps(post_data).encode("utf-8")

        req = urllib.request.Request(
            "https://api.linkedin.com/v2/ugcPosts",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            post_id = result.get("id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}"

            logger.info(f"LinkedIn post published: {post_url}")
            return PublishResult(
                platform="linkedin",
                success=True,
                url=post_url,
                post_id=post_id,
                published_at=datetime.now().isoformat(),
            )

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            logger.error(f"LinkedIn publish failed: {e.code} - {body[:200]}")
            return PublishResult(
                platform="linkedin",
                success=False,
                error=f"HTTP {e.code}: {body[:200]}",
            )
        except urllib.error.URLError as e:
            logger.error(f"LinkedIn connection error: {e.reason}")
            return PublishResult(
                platform="linkedin",
                success=False,
                error=str(e.reason),
            )

    def _upload_image(self, image_path: str) -> Optional[str]:
        """Upload an image to LinkedIn for use in a post.

        LinkedIn image upload is a two-step process:
        1. Register the upload to get an upload URL
        2. Upload the binary image data

        Args:
            image_path: Path to the image file

        Returns:
            Image asset URN or None
        """
        author = f"urn:li:organization:{self.organization_id}"

        # Step 1: Register upload
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        data = json.dumps(register_data).encode("utf-8")

        req = urllib.request.Request(
            "https://api.linkedin.com/v2/assets?action=registerUpload",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"LinkedIn image register failed: {e}")
            return None

        upload_url = (
            result.get("value", {})
            .get("uploadMechanism", {})
            .get("com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {})
            .get("uploadUrl")
        )
        asset = result.get("value", {}).get("asset")

        if not upload_url or not asset:
            logger.error("Failed to get upload URL from LinkedIn")
            return None

        # Step 2: Upload image
        with open(image_path, "rb") as f:
            image_data = f.read()

        req = urllib.request.Request(
            upload_url,
            data=image_data,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream",
            },
            method="PUT",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                logger.info(f"LinkedIn image uploaded: {asset}")
                return asset
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"LinkedIn image upload failed: {e}")
            return None
