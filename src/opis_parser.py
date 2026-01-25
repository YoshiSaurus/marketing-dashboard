"""OPIS (Oil Price Information Service) fuel pricing data parser."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SupplierPrice:
    """Individual supplier price entry."""
    supplier: str
    terms: str
    unl: Optional[float] = None
    unl_move: Optional[float] = None
    mid: Optional[float] = None
    mid_move: Optional[float] = None
    pre: Optional[float] = None
    pre_move: Optional[float] = None
    no2: Optional[float] = None
    no2_move: Optional[float] = None
    no1: Optional[float] = None
    no1_move: Optional[float] = None
    jet: Optional[float] = None
    jet_move: Optional[float] = None
    date: Optional[str] = None
    time: Optional[str] = None


@dataclass
class RackPrices:
    """Rack price summary (LOW, HIGH, AVG)."""
    low: Optional[float] = None
    high: Optional[float] = None
    avg: Optional[float] = None


@dataclass
class ProductPricing:
    """Pricing data for a single product type."""
    product_type: str
    location: str
    timestamp: str
    rvp: Optional[str] = None
    suppliers: list[SupplierPrice] = field(default_factory=list)
    rack_prices: dict[str, RackPrices] = field(default_factory=dict)
    spot_price: Optional[float] = None
    spot_location: Optional[str] = None
    branded_rack: Optional[RackPrices] = None
    unbranded_rack: Optional[RackPrices] = None
    contract_avg: Optional[float] = None
    contract_low: Optional[float] = None
    contract_high: Optional[float] = None


@dataclass
class RetailPrices:
    """Retail pricing data for a location."""
    location: str
    low_retail: Optional[float] = None
    avg_retail: Optional[float] = None
    low_retail_ex_tax: Optional[float] = None
    avg_retail_ex_tax: Optional[float] = None


@dataclass
class OPISData:
    """Complete parsed OPIS data from an email."""
    account_number: Optional[str] = None
    report_date: Optional[str] = None
    locations: list[str] = field(default_factory=list)
    products: list[ProductPricing] = field(default_factory=list)
    retail_prices: list[RetailPrices] = field(default_factory=list)


class OPISParser:
    """Parser for OPIS wholesale fuel pricing emails."""

    # Product type patterns
    PRODUCT_PATTERNS = {
        'conv_clear': r'\*\*OPIS GROSS CONV\. CLEAR PRICES\*\*',
        'cbob_ethanol': r'\*\*OPIS GROSS CBOB ETHANOL\(10%\) PRICES\*\*',
        'uls_distillate': r'\*\*OPIS GROSS ULTRA LOW SULFUR DISTILLATE PRICES\*\*',
        'uls_red_dye': r'\*\*OPIS GROSS ULTRA LOW SULFUR RED DYE DISTILLATE PRICES\*\*',
        'uls_winter': r'\*\*OPIS GROSS ULTRA LOW SULFUR WINTER DISTILLATE PRICES\*\*',
        'uls_red_winter': r'\*\*OPIS GROSS ULTRA LOW SULFUR RED DYE WINTER DISTILLATE PRICES\*\*',
        'specialty': r'\*\*OPIS GROSS SPECIALTY DISTILLATE PRICES\*\*',
        'biodiesel_b0_5': r'\*\*OPIS GROSS WHOLESALE B0-5 SME BIODIESEL PRICES\*\*',
        'biodiesel_b2': r'\*\*OPIS GROSS WHOLESALE B2 SME BIODIESEL PRICES\*\*',
        'biodiesel_b5': r'\*\*OPIS GROSS WHOLESALE B5 SME BIODIESEL PRICES\*\*',
        'e70': r'\*\*OPIS GROSS E-70 PRICES\*\*',
    }

    PRODUCT_DISPLAY_NAMES = {
        'conv_clear': 'Conventional Clear Gasoline',
        'cbob_ethanol': 'CBOB Ethanol (10%)',
        'uls_distillate': 'Ultra Low Sulfur Diesel',
        'uls_red_dye': 'ULS Red Dye Diesel',
        'uls_winter': 'ULS Winter Diesel',
        'uls_red_winter': 'ULS Red Dye Winter Diesel',
        'specialty': 'Specialty Distillate (Jet)',
        'biodiesel_b0_5': 'Biodiesel B0-5 SME',
        'biodiesel_b2': 'Biodiesel B2 SME',
        'biodiesel_b5': 'Biodiesel B5 SME',
        'e70': 'E-70',
    }

    def parse(self, email_body: str) -> OPISData:
        """Parse OPIS email body into structured data.

        Args:
            email_body: Raw email body text

        Returns:
            OPISData object with parsed pricing information
        """
        data = OPISData()

        # Extract account number
        account_match = re.search(r'Account\s*#(\d+)', email_body)
        if account_match:
            data.account_number = account_match.group(1)

        # Extract report date from first timestamp
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}\s+EST', email_body)
        if date_match:
            data.report_date = date_match.group(1)

        # Find all locations
        location_pattern = r'^([A-Z]+(?:\s+[A-Z]+)*,\s*[A-Z]{2})\s+\d{4}-\d{2}-\d{2}'
        locations = set(re.findall(location_pattern, email_body, re.MULTILINE))
        data.locations = sorted(list(locations))

        # Parse each product section
        for product_key, pattern in self.PRODUCT_PATTERNS.items():
            products = self._parse_product_sections(email_body, product_key, pattern)
            data.products.extend(products)

        # Parse retail prices
        data.retail_prices = self._parse_retail_prices(email_body)

        return data

    def _parse_product_sections(self, email_body: str, product_key: str,
                                 pattern: str) -> list[ProductPricing]:
        """Parse all sections for a specific product type.

        Args:
            email_body: Raw email body
            product_key: Product type key
            pattern: Regex pattern to find product header

        Returns:
            List of ProductPricing objects
        """
        products = []

        # Find all occurrences of this product type
        matches = list(re.finditer(pattern, email_body))

        for match in matches:
            start_pos = match.start()

            # Find the location header before this product
            text_before = email_body[:start_pos]
            location_match = re.search(
                r'([A-Z]+(?:\s+[A-Z]+)*,\s*[A-Z]{2})\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+EST)',
                text_before[::-1][:500][::-1]  # Look at last 500 chars before
            )

            # Actually search forward from the start
            loc_search = email_body[max(0, start_pos - 200):start_pos]
            location_match = re.search(
                r'([A-Z]+(?:\s+[A-Z]+)*,\s*[A-Z]{2})\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+EST)',
                loc_search
            )

            location = location_match.group(1) if location_match else 'Unknown'
            timestamp = location_match.group(2) if location_match else ''

            # Extract RVP if present
            rvp_match = re.search(r'(\d+\.\d+)\s*RVP', email_body[start_pos:start_pos + 200])
            rvp = rvp_match.group(1) if rvp_match else None

            # Find end of this section (next location header or product header or EOF)
            end_pos = len(email_body)
            next_section = re.search(
                r'(?:[A-Z]+(?:\s+[A-Z]+)*,\s*[A-Z]{2}\s+\d{4}-\d{2}-\d{2}|\*\*OPIS)',
                email_body[match.end():]
            )
            if next_section:
                end_pos = match.end() + next_section.start()

            section_text = email_body[start_pos:end_pos]

            # Parse the section
            product = ProductPricing(
                product_type=product_key,
                location=location,
                timestamp=timestamp,
                rvp=rvp
            )

            # Parse supplier prices
            product.suppliers = self._parse_supplier_prices(section_text, product_key)

            # Parse rack summaries
            product.rack_prices = self._parse_rack_prices(section_text)

            # Parse spot prices
            spot_match = re.search(r'FOB\s+(\w+)\s+([\d.]+)', section_text)
            if spot_match:
                product.spot_location = spot_match.group(1)
                product.spot_price = float(spot_match.group(2))

            # Parse branded rack
            brd_low = re.search(r'BRD LOW RACK\s+([\d.]+)', section_text)
            brd_high = re.search(r'BRD HIGH RACK\s+([\d.]+)', section_text)
            brd_avg = re.search(r'BRD RACK AVG\s+([\d.]+)', section_text)
            if brd_low or brd_high or brd_avg:
                product.branded_rack = RackPrices(
                    low=float(brd_low.group(1)) if brd_low else None,
                    high=float(brd_high.group(1)) if brd_high else None,
                    avg=float(brd_avg.group(1)) if brd_avg else None
                )

            # Parse unbranded rack
            ubd_low = re.search(r'UBD LOW RACK\s+([\d.]+)', section_text)
            ubd_high = re.search(r'UBD HIGH RACK\s+([\d.]+)', section_text)
            ubd_avg = re.search(r'UBD RACK AVG\s+([\d.]+)', section_text)
            if ubd_low or ubd_high or ubd_avg:
                product.unbranded_rack = RackPrices(
                    low=float(ubd_low.group(1)) if ubd_low else None,
                    high=float(ubd_high.group(1)) if ubd_high else None,
                    avg=float(ubd_avg.group(1)) if ubd_avg else None
                )

            # Parse contract prices
            cont_avg = re.search(r'CONT AVG-\d{2}/\d{2}\s+([\d.]+)', section_text)
            cont_low = re.search(r'CONT LOW-\d{2}/\d{2}\s+([\d.]+)', section_text)
            cont_high = re.search(r'CONT HIGH-\d{2}/\d{2}\s+([\d.]+)', section_text)
            product.contract_avg = float(cont_avg.group(1)) if cont_avg else None
            product.contract_low = float(cont_low.group(1)) if cont_low else None
            product.contract_high = float(cont_high.group(1)) if cont_high else None

            products.append(product)

        return products

    def _parse_supplier_prices(self, section_text: str, product_key: str) -> list[SupplierPrice]:
        """Parse individual supplier price lines.

        Args:
            section_text: Text of the product section
            product_key: Product type key

        Returns:
            List of SupplierPrice objects
        """
        suppliers = []

        # Pattern for supplier lines (e.g., "Valero     b 1-10  208.03  - 1.43")
        # Supplier names: Valero, PSX, DKTS, Cenex, XOM, Chevron
        supplier_pattern = r'^(Valero|PSX|DKTS|Cenex|XOM|Chevron)\s+([bu])\s+([\w-]+)\s+([\d.]+)\s+([+-]?\s*[\d.]+)?'

        for line in section_text.split('\n'):
            match = re.match(supplier_pattern, line.strip())
            if match:
                supplier = SupplierPrice(
                    supplier=match.group(1),
                    terms=f"{match.group(2)} {match.group(3)}"
                )

                # Parse the first price column
                price = float(match.group(4))
                move_str = match.group(5)
                move = None
                if move_str:
                    move_str = move_str.replace(' ', '')
                    try:
                        move = float(move_str)
                    except ValueError:
                        pass

                # Assign to appropriate field based on product type
                if product_key in ['conv_clear', 'cbob_ethanol', 'e70']:
                    supplier.unl = price
                    supplier.unl_move = move
                elif product_key == 'specialty':
                    supplier.jet = price
                    supplier.jet_move = move
                else:
                    supplier.no2 = price
                    supplier.no2_move = move

                # Parse date/time at end of line
                datetime_match = re.search(r'(\d{2}/\d{2})\s+(\d{2}:\d{2})', line)
                if datetime_match:
                    supplier.date = datetime_match.group(1)
                    supplier.time = datetime_match.group(2)

                suppliers.append(supplier)

        return suppliers

    def _parse_rack_prices(self, section_text: str) -> dict[str, RackPrices]:
        """Parse rack price summary lines.

        Args:
            section_text: Text of the product section

        Returns:
            Dictionary mapping grade to RackPrices
        """
        rack_prices = {}

        # Parse main rack prices
        low_match = re.search(r'^LOW RACK\s+([\d.]+)', section_text, re.MULTILINE)
        high_match = re.search(r'^HIGH RACK\s+([\d.]+)', section_text, re.MULTILINE)
        avg_match = re.search(r'^RACK AVG\s+([\d.]+)', section_text, re.MULTILINE)

        if low_match or high_match or avg_match:
            rack_prices['primary'] = RackPrices(
                low=float(low_match.group(1)) if low_match else None,
                high=float(high_match.group(1)) if high_match else None,
                avg=float(avg_match.group(1)) if avg_match else None
            )

        return rack_prices

    def _parse_retail_prices(self, email_body: str) -> list[RetailPrices]:
        """Parse retail price sections.

        Args:
            email_body: Raw email body

        Returns:
            List of RetailPrices objects
        """
        retail_list = []

        # Find retail sections
        retail_pattern = r'([A-Z]+(?:\s+[A-Z]+)*,\s*[A-Z]{2})\s*\n\s*LOW RETAIL\s+([\d.]+)'
        matches = re.finditer(retail_pattern, email_body)

        for match in matches:
            location = match.group(1)
            start_pos = match.start()

            # Extract section
            section_end = email_body.find('\n\n', start_pos + 50)
            if section_end == -1:
                section_end = start_pos + 300
            section = email_body[start_pos:section_end]

            retail = RetailPrices(location=location)

            low_match = re.search(r'LOW RETAIL\s+([\d.]+)', section)
            avg_match = re.search(r'AVG RETAIL\s+([\d.]+)', section)
            low_ex_match = re.search(r'LOW RETAIL EX-TAX\s+([\d.]+)', section)
            avg_ex_match = re.search(r'AVG RETAIL EX-TAX\s+([\d.]+)', section)

            retail.low_retail = float(low_match.group(1)) if low_match else None
            retail.avg_retail = float(avg_match.group(1)) if avg_match else None
            retail.low_retail_ex_tax = float(low_ex_match.group(1)) if low_ex_match else None
            retail.avg_retail_ex_tax = float(avg_ex_match.group(1)) if avg_ex_match else None

            retail_list.append(retail)

        return retail_list

    def get_summary(self, data: OPISData) -> dict:
        """Generate a summary of key prices from parsed OPIS data.

        Args:
            data: Parsed OPISData object

        Returns:
            Dictionary with key price summaries by location and product
        """
        summary = {
            'report_date': data.report_date,
            'account': data.account_number,
            'locations': {}
        }

        for location in data.locations:
            summary['locations'][location] = {
                'products': {},
                'retail': None
            }

            # Get products for this location
            for product in data.products:
                if product.location == location:
                    product_name = self.PRODUCT_DISPLAY_NAMES.get(
                        product.product_type, product.product_type
                    )

                    rack = product.rack_prices.get('primary', RackPrices())
                    summary['locations'][location]['products'][product_name] = {
                        'rack_low': rack.low,
                        'rack_high': rack.high,
                        'rack_avg': rack.avg,
                        'spot_price': product.spot_price,
                        'branded_avg': product.branded_rack.avg if product.branded_rack else None,
                        'unbranded_avg': product.unbranded_rack.avg if product.unbranded_rack else None,
                    }

            # Get retail for this location
            for retail in data.retail_prices:
                if retail.location == location:
                    summary['locations'][location]['retail'] = {
                        'avg_retail': retail.avg_retail,
                        'low_retail': retail.low_retail,
                        'avg_ex_tax': retail.avg_retail_ex_tax,
                        'low_ex_tax': retail.low_retail_ex_tax,
                    }

        return summary
