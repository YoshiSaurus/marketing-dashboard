"""Image generator using Gemini and Banana (Nano Banana) for AI-generated visuals.

Generates images for blog posts and LinkedIn posts using a combination of:
- Google Gemini for image generation
- Banana.dev (Nano Banana) for Stable Diffusion-based generation
- Slack reply images that can be composited
"""

import base64
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
class GeneratedImage:
    """A generated image result."""
    file_path: str
    prompt: str
    generator: str  # "gemini", "banana", "slack_reply"
    width: int = 0
    height: int = 0
    created_at: str = ""


class ImageGenerator:
    """Generates images using Gemini and Banana.dev APIs."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        banana_api_key: Optional[str] = None,
        output_dir: str = "generated_images",
    ):
        """Initialize the image generator.

        Args:
            gemini_api_key: Google Gemini API key
            banana_api_key: Banana.dev API key for Nano Banana
            output_dir: Directory to save generated images
        """
        self.gemini_api_key = gemini_api_key
        self.banana_api_key = banana_api_key
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_image(
        self,
        prompt: str,
        style: str = "professional",
        suggestion_id: str = "",
    ) -> Optional[GeneratedImage]:
        """Generate an image using the best available generator.

        Tries Gemini first, then falls back to Banana.

        Args:
            prompt: Image generation prompt
            style: Style modifier ("professional", "tech", "editorial")
            suggestion_id: Content suggestion ID for file naming

        Returns:
            GeneratedImage or None on failure
        """
        enhanced_prompt = self._enhance_prompt(prompt, style)

        # Try Gemini first
        if self.gemini_api_key:
            result = self._generate_with_gemini(enhanced_prompt, suggestion_id)
            if result:
                return result

        # Fall back to Banana
        if self.banana_api_key:
            result = self._generate_with_banana(enhanced_prompt, suggestion_id)
            if result:
                return result

        logger.warning("No image generator available or all generators failed")
        return None

    def download_slack_image(
        self,
        image_url: str,
        slack_bot_token: str,
        suggestion_id: str = "",
    ) -> Optional[GeneratedImage]:
        """Download an image from a Slack reply.

        Args:
            image_url: Slack file URL
            slack_bot_token: Bot token for authentication
            suggestion_id: Content suggestion ID for file naming

        Returns:
            GeneratedImage or None on failure
        """
        req = urllib.request.Request(
            image_url,
            headers={"Authorization": f"Bearer {slack_bot_token}"},
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                image_data = response.read()
                content_type = response.headers.get("Content-Type", "image/jpeg")

                ext = "jpg"
                if "png" in content_type:
                    ext = "png"
                elif "gif" in content_type:
                    ext = "gif"
                elif "webp" in content_type:
                    ext = "webp"

                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"slack_{suggestion_id}_{timestamp}.{ext}"
                filepath = os.path.join(self.output_dir, filename)

                with open(filepath, "wb") as f:
                    f.write(image_data)

                return GeneratedImage(
                    file_path=filepath,
                    prompt="Slack reply image",
                    generator="slack_reply",
                    created_at=datetime.now().isoformat(),
                )

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Failed to download Slack image: {e}")
            return None

    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance the image prompt with style modifiers.

        Args:
            prompt: Base prompt
            style: Style to apply

        Returns:
            Enhanced prompt
        """
        style_modifiers = {
            "professional": (
                "Professional corporate style, clean modern design, "
                "subtle blue and white color scheme, high quality, "
                "suitable for business blog and LinkedIn"
            ),
            "tech": (
                "Modern technology aesthetic, digital and data visualization elements, "
                "futuristic feel, clean lines, dark blue and cyan accents"
            ),
            "editorial": (
                "Editorial magazine style, high-quality photography feel, "
                "balanced composition, warm professional lighting"
            ),
        }

        modifier = style_modifiers.get(style, style_modifiers["professional"])
        return f"{prompt}. {modifier}"

    def _generate_with_gemini(
        self, prompt: str, suggestion_id: str
    ) -> Optional[GeneratedImage]:
        """Generate image using Google Gemini Imagen API.

        Args:
            prompt: Image generation prompt
            suggestion_id: ID for file naming

        Returns:
            GeneratedImage or None
        """
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                    "role": "user",
                }
            ],
            "generationConfig": {
                "responseModalities": ["image", "text"],
                "imageSizeOptions": {
                    "aspectRatio": "16:9",
                },
            },
        }

        data = json.dumps(payload).encode("utf-8")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}"
        )

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))

            # Extract image from response
            candidates = result.get("candidates", [])
            if not candidates:
                logger.error("No candidates in Gemini response")
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                inline_data = part.get("inlineData")
                if inline_data and inline_data.get("mimeType", "").startswith("image/"):
                    image_bytes = base64.b64decode(inline_data["data"])
                    mime = inline_data["mimeType"]
                    ext = "png" if "png" in mime else "jpg"

                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"gemini_{suggestion_id}_{timestamp}.{ext}"
                    filepath = os.path.join(self.output_dir, filename)

                    with open(filepath, "wb") as f:
                        f.write(image_bytes)

                    logger.info(f"Gemini image generated: {filepath}")
                    return GeneratedImage(
                        file_path=filepath,
                        prompt=prompt,
                        generator="gemini",
                        created_at=datetime.now().isoformat(),
                    )

            logger.warning("No image found in Gemini response")
            return None

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def _generate_with_banana(
        self, prompt: str, suggestion_id: str
    ) -> Optional[GeneratedImage]:
        """Generate image using Banana.dev (Nano Banana) API.

        Uses Stable Diffusion via Banana serverless GPU inference.

        Args:
            prompt: Image generation prompt
            suggestion_id: ID for file naming

        Returns:
            GeneratedImage or None
        """
        payload = {
            "prompt": prompt,
            "negative_prompt": (
                "blurry, low quality, distorted, watermark, text overlay, "
                "cartoon, anime, sketch, drawing"
            ),
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "width": 1024,
            "height": 576,  # 16:9 aspect ratio
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            "https://api.banana.dev/start/v4/",
            data=json.dumps({
                "apiKey": self.banana_api_key,
                "modelKey": "sd-xl",  # Stable Diffusion XL
                "modelInputs": payload,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))

            # Extract image from response
            model_outputs = result.get("modelOutputs", [])
            if not model_outputs:
                logger.error("No model outputs in Banana response")
                return None

            image_b64 = model_outputs[0].get("image_base64") or model_outputs[0].get("image")
            if not image_b64:
                logger.error("No image data in Banana response")
                return None

            image_bytes = base64.b64decode(image_b64)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"banana_{suggestion_id}_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Banana image generated: {filepath}")
            return GeneratedImage(
                file_path=filepath,
                prompt=prompt,
                generator="banana",
                width=1024,
                height=576,
                created_at=datetime.now().isoformat(),
            )

        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logger.error(f"Banana API error: {e}")
            return None
