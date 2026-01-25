"""
Data storage module for OPIS pricing data.

Architecture:
    Raw Capture → Extracted Rows → Derived Views

1. Raw Capture: Lossless, append-only storage of original emails
2. Extracted Rows: Row-level parsing without normalization
3. Derived Views: Normalized, opinionated views for analysis

This separation enables:
- Reparsing with upgraded parsers
- Audit trails
- ML model training on raw data
- Compliance with licensing restrictions
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from pathlib import Path


@dataclass
class RawCapture:
    """Immutable raw capture of an OPIS email.

    This is the source of truth - never modified after creation.
    """
    id: str  # SHA256 of raw_text
    source: str  # "OPIS"
    delivery_channel: str  # "email"
    received_at: str  # ISO timestamp
    sender: str
    subject: str
    market: str  # "Group 3" etc
    raw_text: str  # Exact email body - never modified
    checksum: str  # SHA256 of raw_text for integrity

    # Metadata
    account_number: Optional[str] = None
    locations: list[str] = field(default_factory=list)

    # License tracking
    license_restriction: str = "internal_use_only"
    source_attribution: str = "Oil Price Information Service (OPIS)"


@dataclass
class ExtractedRow:
    """Single extracted price row - preserves semantic ambiguity.

    Every row from the email becomes one fact. Summary rows (LOW RACK,
    RACK AVG, etc.) coexist with vendor rows.
    """
    # Source linkage
    capture_id: str  # Links to RawCapture.id
    row_index: int  # Position in original email

    # Location context
    city: str  # "AMARILLO, TX"

    # Product context (preserved as-is from email)
    product_group: str  # "GROSS CONV. CLEAR", "GROSS CBOB ETHANOL(10%)"
    product_variant: Optional[str] = None
    rvp: Optional[str] = None  # "9.0" etc

    # Row identification
    row_type: str  # "vendor", "summary", "spot", "retail"
    row_label: str  # "Valero", "LOW RACK", "RACK AVG", "FOB AMARILLO"

    # Vendor-specific (if row_type == "vendor")
    vendor: Optional[str] = None
    terms: Optional[str] = None  # "b 1-10", "u N-10"

    # Price columns - preserved as they appear
    # For gasoline: Unl, Mid, Pre
    # For diesel: No.2, No.1, Pre
    price_columns: dict = field(default_factory=dict)
    # Example: {"Unl": 208.03, "Unl_move": -1.43, "Pre": 265.96, "Pre_move": -3.50}

    # Timing
    reported_date: Optional[str] = None  # "01/22"
    reported_time: Optional[str] = None  # "18:00"
    snapshot_timestamp: Optional[str] = None  # Full timestamp from header

    # Raw preservation
    raw_row_text: str = ""  # Original row text for audit

    # Price metadata
    price_unit: str = "cents_per_gallon"


@dataclass
class RetailRow:
    """Extracted retail price row."""
    capture_id: str
    city: str
    row_label: str  # "LOW RETAIL", "AVG RETAIL", "LOW RETAIL EX-TAX"
    price: float
    price_unit: str = "cents_per_gallon"
    raw_row_text: str = ""


class OPISDataStore:
    """
    Data store for OPIS pricing data with separation of concerns.

    Storage structure:
        data/
        ├── raw/           # Immutable raw captures (one JSON per email)
        ├── extracted/     # Extracted rows (append-only)
        ├── derived/       # Normalized views (regeneratable)
        └── manifest.json  # Index of all captures
    """

    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self.extracted_path = self.base_path / "extracted"
        self.derived_path = self.base_path / "derived"

        # Create directories
        for path in [self.raw_path, self.extracted_path, self.derived_path]:
            path.mkdir(parents=True, exist_ok=True)

        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        """Load or create the manifest index."""
        manifest_path = self.base_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                return json.load(f)
        return {
            "created_at": datetime.now().isoformat(),
            "captures": [],
            "total_rows_extracted": 0,
            "last_updated": None
        }

    def _save_manifest(self):
        """Save the manifest index."""
        self._manifest["last_updated"] = datetime.now().isoformat()
        with open(self.base_path / "manifest.json", 'w') as f:
            json.dump(self._manifest, f, indent=2)

    def _compute_checksum(self, text: str) -> str:
        """Compute SHA256 checksum of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def capture_exists(self, raw_text: str) -> bool:
        """Check if this email has already been captured."""
        checksum = self._compute_checksum(raw_text)
        return any(c.get('checksum') == checksum for c in self._manifest['captures'])

    def store_raw_capture(
        self,
        raw_text: str,
        sender: str,
        subject: str,
        received_at: Optional[str] = None,
        account_number: Optional[str] = None,
        locations: Optional[list[str]] = None,
        market: str = "Group 3"
    ) -> RawCapture:
        """
        Store a raw email capture (lossless, immutable).

        Args:
            raw_text: Exact email body
            sender: Sender email address
            subject: Email subject
            received_at: ISO timestamp when received
            account_number: OPIS account number if found
            locations: List of locations in the email
            market: Market identifier

        Returns:
            RawCapture object with assigned ID
        """
        checksum = self._compute_checksum(raw_text)
        capture_id = checksum[:16]  # Use first 16 chars as ID

        # Check for duplicates
        if self.capture_exists(raw_text):
            raise ValueError(f"Duplicate capture detected (checksum: {checksum[:8]}...)")

        capture = RawCapture(
            id=capture_id,
            source="OPIS",
            delivery_channel="email",
            received_at=received_at or datetime.now().isoformat(),
            sender=sender,
            subject=subject,
            market=market,
            raw_text=raw_text,
            checksum=checksum,
            account_number=account_number,
            locations=locations or []
        )

        # Save raw capture (immutable)
        capture_file = self.raw_path / f"{capture_id}.json"
        with open(capture_file, 'w') as f:
            json.dump(asdict(capture), f, indent=2)

        # Update manifest
        self._manifest['captures'].append({
            'id': capture_id,
            'checksum': checksum,
            'received_at': capture.received_at,
            'locations': capture.locations,
            'subject': subject
        })
        self._save_manifest()

        return capture

    def store_extracted_rows(
        self,
        capture_id: str,
        rows: list[ExtractedRow],
        retail_rows: Optional[list[RetailRow]] = None
    ):
        """
        Store extracted rows linked to a raw capture.

        Args:
            capture_id: ID of the source RawCapture
            rows: List of ExtractedRow objects
            retail_rows: Optional list of RetailRow objects
        """
        # Store in JSONL format (append-friendly)
        rows_file = self.extracted_path / f"{capture_id}_rows.jsonl"

        with open(rows_file, 'w') as f:
            for row in rows:
                f.write(json.dumps(asdict(row)) + '\n')

        if retail_rows:
            retail_file = self.extracted_path / f"{capture_id}_retail.jsonl"
            with open(retail_file, 'w') as f:
                for row in retail_rows:
                    f.write(json.dumps(asdict(row)) + '\n')

        # Update manifest
        self._manifest['total_rows_extracted'] += len(rows)
        if retail_rows:
            self._manifest['total_rows_extracted'] += len(retail_rows)
        self._save_manifest()

    def get_raw_capture(self, capture_id: str) -> Optional[dict]:
        """Retrieve a raw capture by ID."""
        capture_file = self.raw_path / f"{capture_id}.json"
        if capture_file.exists():
            with open(capture_file, 'r') as f:
                return json.load(f)
        return None

    def get_extracted_rows(self, capture_id: str) -> list[dict]:
        """Retrieve extracted rows for a capture."""
        rows_file = self.extracted_path / f"{capture_id}_rows.jsonl"
        rows = []
        if rows_file.exists():
            with open(rows_file, 'r') as f:
                for line in f:
                    if line.strip():
                        rows.append(json.loads(line))
        return rows

    def get_all_captures(self) -> list[dict]:
        """Get manifest of all captures."""
        return self._manifest.get('captures', [])

    def get_statistics(self) -> dict:
        """Get storage statistics."""
        return {
            'total_captures': len(self._manifest.get('captures', [])),
            'total_rows_extracted': self._manifest.get('total_rows_extracted', 0),
            'last_updated': self._manifest.get('last_updated'),
            'storage_path': str(self.base_path)
        }


class DerivedViews:
    """
    Generate normalized, opinionated views from extracted data.

    These views are:
    - Reproducible from raw data
    - Versioned
    - Disposable (can be regenerated)
    """

    def __init__(self, store: OPISDataStore):
        self.store = store

    def generate_rack_averages(self) -> list[dict]:
        """
        Generate normalized rack average prices.

        Returns list of:
        {
            "location": "Amarillo, TX",
            "product": "ULSD",
            "benchmark": "OPIS_RACK_AVG",
            "price": 232.73,
            "date": "2026-01-22"
        }
        """
        results = []

        for capture_info in self.store.get_all_captures():
            capture_id = capture_info['id']
            rows = self.store.get_extracted_rows(capture_id)

            for row in rows:
                if row.get('row_label') == 'RACK AVG':
                    # Normalize product name
                    product = self._normalize_product(row.get('product_group', ''))

                    # Extract prices from columns
                    for col_name, price in row.get('price_columns', {}).items():
                        if not col_name.endswith('_move') and price is not None:
                            results.append({
                                'location': row.get('city'),
                                'product': product,
                                'price_column': col_name,
                                'benchmark': 'OPIS_RACK_AVG',
                                'price': price,
                                'date': row.get('reported_date'),
                                'capture_id': capture_id
                            })

        return results

    def generate_price_history(self, location: str, product: str) -> list[dict]:
        """Generate price history for a specific location/product."""
        history = []
        rack_avgs = self.generate_rack_averages()

        for record in rack_avgs:
            if (record['location'] == location and
                record['product'] == product):
                history.append({
                    'date': record['date'],
                    'price': record['price'],
                    'benchmark': record['benchmark']
                })

        return sorted(history, key=lambda x: x['date'] or '')

    def _normalize_product(self, product_group: str) -> str:
        """Normalize product group to standard name."""
        pg = product_group.upper()

        if 'CONV' in pg and 'CLEAR' in pg:
            return 'Conventional Gasoline'
        elif 'CBOB' in pg or 'ETHANOL' in pg:
            return 'CBOB Ethanol 10%'
        elif 'RED DYE' in pg and 'WINTER' in pg:
            return 'ULS Red Dye Winter Diesel'
        elif 'RED DYE' in pg:
            return 'ULS Red Dye Diesel'
        elif 'WINTER' in pg:
            return 'ULS Winter Diesel'
        elif 'ULTRA LOW SULFUR' in pg or 'ULS' in pg:
            return 'ULSD'
        elif 'SPECIALTY' in pg or 'JET' in pg:
            return 'Jet Fuel'
        elif 'BIODIESEL' in pg:
            if 'B5' in pg:
                return 'Biodiesel B5'
            elif 'B2' in pg:
                return 'Biodiesel B2'
            else:
                return 'Biodiesel'
        else:
            return product_group

    def save_derived_view(self, name: str, data: list[dict]):
        """Save a derived view to disk."""
        view_file = self.store.derived_path / f"{name}.json"
        with open(view_file, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'record_count': len(data),
                'data': data
            }, f, indent=2)
