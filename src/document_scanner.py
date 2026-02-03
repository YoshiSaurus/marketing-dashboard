"""Document scanner for extracting BOL (Bill of Lading) fields using Claude Vision API."""

import base64
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class ExtractedBOLData:
    """Extracted Bill of Lading data fields."""
    bill_to: Optional[str] = None
    ship_to: Optional[str] = None
    bol_number: Optional[str] = None
    site_name: Optional[str] = None
    gross_gallons: Optional[str] = None
    net_gallons: Optional[str] = None
    product_name: Optional[str] = None
    terminal_name: Optional[str] = None
    site_addresses: Optional[str] = None
    carrier_name: Optional[str] = None


@dataclass
class ModelEvaluation:
    """Model's self-evaluation of extraction quality."""
    overall_confidence: str  # high/medium/low
    clarity_probability: float  # 0.0-1.0
    fields_found: int
    fields_missing: int
    document_quality: str  # excellent/good/fair/poor
    notes: str


@dataclass
class ScanResult:
    """Complete scan result with extracted data and evaluation."""
    extracted_data: ExtractedBOLData
    model_evaluation: ModelEvaluation

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "extracted_data": asdict(self.extracted_data),
            "model_evaluation": asdict(self.model_evaluation)
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class DocumentScanner:
    """Scanner for extracting structured data from BOL documents using Claude Vision."""

    # Fields to extract from BOL documents
    EXTRACTION_FIELDS = [
        "bill_to", "ship_to", "bol_number", "site_name",
        "gross_gallons", "net_gallons", "product_name",
        "terminal_name", "site_addresses", "carrier_name"
    ]

    EXTRACTION_PROMPT = """You are a document scanning assistant. Analyze this Bill of Lading (BOL) or delivery document and extract the following 10 specific fields:

1. Bill To - The billing address/company
2. Ship To - The shipping/delivery address
3. BOL number - Bill of Lading number (may be labeled as BOL#, Folio, or Manifest No.)
4. Site name - The delivery site name (often appears with Ship To)
5. Gross gallons - Total gross gallons
6. Net Gallons - Net gallons after temperature adjustment
7. Product name - The fuel/product being delivered (e.g., gasoline, diesel)
8. Terminal name - The terminal/origin location
9. Site addresses - All addresses mentioned in the document
10. Carrier name - The carrier/trucking company

IMPORTANT EXTRACTION GUIDELINES:
- Extract information exactly as it appears in the document
- If a field is not present, return null for that field
- For numerical values (gallons, BOL numbers), preserve the exact format
- For addresses, include the complete address as shown
- Distinguish between "Bill To" and "Ship To" - these are often different
- Look for handwritten notes that may contain compartment-level gross/net gallons

Return ONLY a valid JSON object with this exact structure (no other text):
{
  "extracted_data": {
    "bill_to": "value or null",
    "ship_to": "value or null",
    "bol_number": "value or null",
    "site_name": "value or null",
    "gross_gallons": "value or null",
    "net_gallons": "value or null",
    "product_name": "value or null",
    "terminal_name": "value or null",
    "site_addresses": "value or null",
    "carrier_name": "value or null"
  },
  "model_evaluation": {
    "overall_confidence": "high/medium/low",
    "clarity_probability": 0.0-1.0,
    "fields_found": number,
    "fields_missing": number,
    "document_quality": "excellent/good/fair/poor",
    "notes": "observations about the extraction"
  }
}

Confidence scoring:
- "high" if 8+ fields found clearly
- "medium" if 5-7 fields found
- "low" if fewer than 5 fields found

Now analyze the document and extract the fields."""

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize the document scanner.

        Args:
            anthropic_api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter required")

        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"  # Vision-capable model

    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """Encode image file to base64.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (base64_data, media_type)
        """
        path = Path(image_path)
        suffix = path.suffix.lower()

        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }

        media_type = media_type_map.get(suffix, "image/jpeg")

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return image_data, media_type

    def _encode_image_bytes(self, image_bytes: bytes, media_type: str = "image/jpeg") -> str:
        """Encode image bytes to base64.

        Args:
            image_bytes: Raw image bytes
            media_type: MIME type of the image

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode("utf-8")

    def _call_claude_api(self, image_data: str, media_type: str) -> dict:
        """Call Claude API with image for document extraction.

        Args:
            image_data: Base64 encoded image data
            media_type: MIME type of the image

        Returns:
            Parsed JSON response from Claude
        """
        import urllib.request
        import urllib.error

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": self.EXTRACTION_PROMPT
                        }
                    ]
                }
            ]
        }

        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"Claude API error: {e.code} - {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Claude API connection error: {e.reason}")

    def _parse_response(self, api_response: dict) -> ScanResult:
        """Parse Claude API response into ScanResult.

        Args:
            api_response: Raw API response from Claude

        Returns:
            Parsed ScanResult
        """
        # Extract text content from response
        content = api_response.get("content", [])
        text_content = ""
        for block in content:
            if block.get("type") == "text":
                text_content = block.get("text", "")
                break

        # Parse JSON from response
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', text_content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")

            extracted = parsed.get("extracted_data", {})
            evaluation = parsed.get("model_evaluation", {})

            return ScanResult(
                extracted_data=ExtractedBOLData(
                    bill_to=extracted.get("bill_to"),
                    ship_to=extracted.get("ship_to"),
                    bol_number=extracted.get("bol_number"),
                    site_name=extracted.get("site_name"),
                    gross_gallons=extracted.get("gross_gallons"),
                    net_gallons=extracted.get("net_gallons"),
                    product_name=extracted.get("product_name"),
                    terminal_name=extracted.get("terminal_name"),
                    site_addresses=extracted.get("site_addresses"),
                    carrier_name=extracted.get("carrier_name")
                ),
                model_evaluation=ModelEvaluation(
                    overall_confidence=evaluation.get("overall_confidence", "low"),
                    clarity_probability=float(evaluation.get("clarity_probability", 0.5)),
                    fields_found=int(evaluation.get("fields_found", 0)),
                    fields_missing=int(evaluation.get("fields_missing", 10)),
                    document_quality=evaluation.get("document_quality", "fair"),
                    notes=evaluation.get("notes", "")
                )
            )
        except (json.JSONDecodeError, ValueError) as e:
            # Return error result if parsing fails
            return ScanResult(
                extracted_data=ExtractedBOLData(),
                model_evaluation=ModelEvaluation(
                    overall_confidence="low",
                    clarity_probability=0.0,
                    fields_found=0,
                    fields_missing=10,
                    document_quality="poor",
                    notes=f"Failed to parse response: {str(e)}. Raw response: {text_content[:500]}"
                )
            )

    def scan_file(self, file_path: str) -> ScanResult:
        """Scan a document file and extract BOL fields.

        Args:
            file_path: Path to the image file

        Returns:
            ScanResult with extracted data and evaluation
        """
        image_data, media_type = self._encode_image(file_path)
        api_response = self._call_claude_api(image_data, media_type)
        return self._parse_response(api_response)

    def scan_bytes(self, image_bytes: bytes, media_type: str = "image/jpeg") -> ScanResult:
        """Scan image bytes and extract BOL fields.

        Args:
            image_bytes: Raw image bytes
            media_type: MIME type of the image

        Returns:
            ScanResult with extracted data and evaluation
        """
        image_data = self._encode_image_bytes(image_bytes, media_type)
        api_response = self._call_claude_api(image_data, media_type)
        return self._parse_response(api_response)

    def scan_base64(self, base64_data: str, media_type: str = "image/jpeg") -> ScanResult:
        """Scan base64 encoded image and extract BOL fields.

        Args:
            base64_data: Base64 encoded image data
            media_type: MIME type of the image

        Returns:
            ScanResult with extracted data and evaluation
        """
        api_response = self._call_claude_api(base64_data, media_type)
        return self._parse_response(api_response)


def format_scan_result_for_slack(result: ScanResult) -> dict:
    """Format scan result as Slack Block Kit message.

    Args:
        result: ScanResult to format

    Returns:
        Slack Block Kit blocks
    """
    data = result.extracted_data
    eval_data = result.model_evaluation

    # Confidence emoji
    confidence_emoji = {
        "high": ":white_check_mark:",
        "medium": ":warning:",
        "low": ":x:"
    }.get(eval_data.overall_confidence, ":question:")

    # Quality emoji
    quality_emoji = {
        "excellent": ":star:",
        "good": ":thumbsup:",
        "fair": ":ok_hand:",
        "poor": ":thumbsdown:"
    }.get(eval_data.document_quality, ":question:")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Document Scan Results",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Confidence:* {confidence_emoji} {eval_data.overall_confidence.upper()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Quality:* {quality_emoji} {eval_data.document_quality.capitalize()}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Fields Found:* {eval_data.fields_found}/10"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Clarity:* {eval_data.clarity_probability:.0%}"
                }
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Extracted Data:*"
            }
        }
    ]

    # Add extracted fields
    field_labels = {
        "bill_to": "Bill To",
        "ship_to": "Ship To",
        "bol_number": "BOL Number",
        "site_name": "Site Name",
        "gross_gallons": "Gross Gallons",
        "net_gallons": "Net Gallons",
        "product_name": "Product",
        "terminal_name": "Terminal",
        "site_addresses": "Addresses",
        "carrier_name": "Carrier"
    }

    for field, label in field_labels.items():
        value = getattr(data, field)
        display_value = value if value else "_Not found_"
        # Truncate long values
        if len(display_value) > 100:
            display_value = display_value[:97] + "..."
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{label}:* {display_value}"
            }
        })

    # Add notes if present
    if eval_data.notes:
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":memo: *Notes:* {eval_data.notes[:300]}"
                    }
                ]
            }
        ])

    return {"blocks": blocks, "text": "Document scan completed"}
