"""Cost data processor for analyzing OPIS fuel pricing data and generating trends."""

import json
import os
from datetime import datetime
from typing import Optional

from .opis_parser import OPISParser, OPISData


class FuelPriceProcessor:
    """Processes OPIS fuel pricing data and generates trend analysis."""

    # Key products to track for trend analysis
    KEY_PRODUCTS = [
        'Conventional Clear Gasoline',
        'CBOB Ethanol (10%)',
        'Ultra Low Sulfur Diesel',
        'ULS Red Dye Diesel',
    ]

    def __init__(self, history_file: str = 'price_history.json'):
        """Initialize the fuel price processor.

        Args:
            history_file: Path to JSON file storing price history
        """
        self.parser = OPISParser()
        self.history_file = history_file
        self._history = self._load_history()

    def _load_history(self) -> dict:
        """Load price history from file.

        Returns:
            Dictionary of historical prices by location and product
        """
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {'prices': {}, 'last_updated': None}

    def _save_history(self) -> None:
        """Save price history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self._history, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save price history: {e}")

    def parse_opis_email(self, email_body: str) -> OPISData:
        """Parse OPIS email body into structured data.

        Args:
            email_body: Raw email body text

        Returns:
            OPISData object with parsed pricing information
        """
        return self.parser.parse(email_body)

    def get_summary(self, data: OPISData) -> dict:
        """Get a summary of the parsed OPIS data.

        Args:
            data: Parsed OPISData object

        Returns:
            Summary dictionary with key prices
        """
        return self.parser.get_summary(data)

    def update_history(self, data: OPISData) -> None:
        """Update price history with new data.

        Args:
            data: Parsed OPISData object
        """
        summary = self.get_summary(data)
        date_key = data.report_date or datetime.now().strftime('%Y-%m-%d')

        if 'prices' not in self._history:
            self._history['prices'] = {}

        for location, loc_data in summary.get('locations', {}).items():
            if location not in self._history['prices']:
                self._history['prices'][location] = {}

            for product, prices in loc_data.get('products', {}).items():
                if product not in self._history['prices'][location]:
                    self._history['prices'][location][product] = []

                # Add new price point
                self._history['prices'][location][product].append({
                    'date': date_key,
                    'rack_avg': prices.get('rack_avg'),
                    'rack_low': prices.get('rack_low'),
                    'rack_high': prices.get('rack_high'),
                    'spot_price': prices.get('spot_price'),
                })

                # Keep only last 30 days of history
                self._history['prices'][location][product] = \
                    self._history['prices'][location][product][-30:]

        self._history['last_updated'] = datetime.now().isoformat()
        self._save_history()

    def calculate_trends(self, data: OPISData) -> dict:
        """Calculate price trends comparing current to historical data.

        Args:
            data: Parsed OPISData object

        Returns:
            Dictionary with trend analysis by location and product
        """
        summary = self.get_summary(data)
        trends = {
            'report_date': data.report_date,
            'locations': {}
        }

        for location, loc_data in summary.get('locations', {}).items():
            trends['locations'][location] = {
                'products': {},
                'retail': loc_data.get('retail')
            }

            for product, prices in loc_data.get('products', {}).items():
                current_avg = prices.get('rack_avg')
                if current_avg is None:
                    continue

                # Get historical data
                historical = self._get_historical_prices(location, product)

                if historical:
                    prev_avg = historical[-1].get('rack_avg') if historical else None
                    week_prices = [h.get('rack_avg') for h in historical[-7:] if h.get('rack_avg')]
                    week_avg = sum(week_prices) / len(week_prices) if week_prices else None

                    day_change = current_avg - prev_avg if prev_avg else None
                    day_change_pct = (day_change / prev_avg * 100) if prev_avg and day_change else None

                    week_change = current_avg - week_avg if week_avg else None
                    week_change_pct = (week_change / week_avg * 100) if week_avg and week_change else None
                else:
                    prev_avg = None
                    week_avg = None
                    day_change = None
                    day_change_pct = None
                    week_change = None
                    week_change_pct = None

                trends['locations'][location]['products'][product] = {
                    'current': {
                        'rack_avg': current_avg,
                        'rack_low': prices.get('rack_low'),
                        'rack_high': prices.get('rack_high'),
                        'spot_price': prices.get('spot_price'),
                        'branded_avg': prices.get('branded_avg'),
                        'unbranded_avg': prices.get('unbranded_avg'),
                    },
                    'previous_day': prev_avg,
                    'week_avg': week_avg,
                    'day_change': round(day_change, 2) if day_change else None,
                    'day_change_pct': round(day_change_pct, 2) if day_change_pct else None,
                    'week_change': round(week_change, 2) if week_change else None,
                    'week_change_pct': round(week_change_pct, 2) if week_change_pct else None,
                    'direction': self._get_direction(day_change_pct),
                }

        return trends

    def _get_historical_prices(self, location: str, product: str) -> list:
        """Get historical prices for a location/product.

        Args:
            location: Location name
            product: Product name

        Returns:
            List of historical price dictionaries
        """
        return self._history.get('prices', {}).get(location, {}).get(product, [])

    def _get_direction(self, change_pct: Optional[float]) -> str:
        """Determine trend direction from percentage change.

        Args:
            change_pct: Percentage change value

        Returns:
            Direction string: 'up', 'down', or 'stable'
        """
        if change_pct is None:
            return 'new'
        if change_pct > 0.5:
            return 'up'
        if change_pct < -0.5:
            return 'down'
        return 'stable'

    def generate_trend_report(self, trends: dict) -> str:
        """Generate a human-readable trend report for email reply.

        Args:
            trends: Dictionary of trend analysis from calculate_trends()

        Returns:
            Formatted string report suitable for email
        """
        report_date = trends.get('report_date', datetime.now().strftime('%Y-%m-%d'))

        lines = [
            f"OPIS Fuel Price Trends Report - {report_date}",
            "=" * 60,
            "",
        ]

        for location, loc_data in trends.get('locations', {}).items():
            lines.extend([
                f"Location: {location}",
                "-" * 60,
                "",
            ])

            # Product prices table header
            lines.append(f"{'Product':<35} {'Rack Avg':>10} {'Change':>10} {'%':>8}")
            lines.append("-" * 65)

            products = loc_data.get('products', {})
            for product_name in self.KEY_PRODUCTS:
                if product_name in products:
                    product = products[product_name]
                    current = product['current']
                    rack_avg = current.get('rack_avg', 0)
                    day_change = product.get('day_change')
                    day_pct = product.get('day_change_pct')

                    change_str = f"{day_change:+.2f}" if day_change is not None else "N/A"
                    pct_str = f"{day_pct:+.2f}%" if day_pct is not None else "N/A"

                    direction = product.get('direction', 'new')
                    indicator = {'up': '(UP)', 'down': '(DOWN)', 'stable': '(--)', 'new': '(NEW)'}

                    lines.append(
                        f"{product_name:<35} {rack_avg:>10.2f} {change_str:>10} {pct_str:>8} {indicator.get(direction, '')}"
                    )

            # Add other products
            for product_name, product in products.items():
                if product_name not in self.KEY_PRODUCTS:
                    current = product['current']
                    rack_avg = current.get('rack_avg', 0)
                    if rack_avg:
                        day_change = product.get('day_change')
                        day_pct = product.get('day_change_pct')
                        change_str = f"{day_change:+.2f}" if day_change is not None else "N/A"
                        pct_str = f"{day_pct:+.2f}%" if day_pct is not None else "N/A"
                        lines.append(
                            f"{product_name:<35} {rack_avg:>10.2f} {change_str:>10} {pct_str:>8}"
                        )

            lines.append("")

            # Retail prices if available
            retail = loc_data.get('retail')
            if retail:
                lines.extend([
                    "Retail Prices:",
                    f"  Average Retail: {retail.get('avg_retail', 'N/A')} cpg",
                    f"  Low Retail: {retail.get('low_retail', 'N/A')} cpg",
                    f"  Average Ex-Tax: {retail.get('avg_ex_tax', 'N/A')} cpg",
                    "",
                ])

            lines.append("")

        # Add insights
        lines.extend([
            "MARKET INSIGHTS",
            "-" * 40,
        ])
        insights = self._generate_insights(trends)
        for insight in insights:
            lines.append(f"  * {insight}")

        lines.extend([
            "",
            "-" * 60,
            "This report was automatically generated from OPIS pricing data.",
            "Prices shown in cents per gallon (cpg).",
            "",
            "Best regards,",
            "Fuel Price Analysis Agent"
        ])

        return "\n".join(lines)

    def _generate_insights(self, trends: dict) -> list[str]:
        """Generate market insights from trend data.

        Args:
            trends: Dictionary of trend analysis

        Returns:
            List of insight strings
        """
        insights = []

        all_changes = []
        for location, loc_data in trends.get('locations', {}).items():
            for product_name, product in loc_data.get('products', {}).items():
                if product_name in self.KEY_PRODUCTS:
                    day_change = product.get('day_change')
                    if day_change is not None:
                        all_changes.append((location, product_name, day_change))

        if all_changes:
            # Find biggest mover
            biggest_up = max(all_changes, key=lambda x: x[2], default=None)
            biggest_down = min(all_changes, key=lambda x: x[2], default=None)

            if biggest_up and biggest_up[2] > 0:
                insights.append(
                    f"Largest increase: {biggest_up[1]} in {biggest_up[0]} "
                    f"(+{biggest_up[2]:.2f} cpg)"
                )

            if biggest_down and biggest_down[2] < 0:
                insights.append(
                    f"Largest decrease: {biggest_down[1]} in {biggest_down[0]} "
                    f"({biggest_down[2]:.2f} cpg)"
                )

            # Overall market direction
            avg_change = sum(c[2] for c in all_changes) / len(all_changes)
            if avg_change > 1:
                insights.append("Overall market trending HIGHER today.")
            elif avg_change < -1:
                insights.append("Overall market trending LOWER today.")
            else:
                insights.append("Market relatively stable compared to yesterday.")

        if not insights:
            insights.append("First report - historical comparison will be available tomorrow.")

        return insights

    def generate_slack_summary(self, trends: dict) -> dict:
        """Generate a summary suitable for Slack notification.

        Args:
            trends: Dictionary of trend analysis

        Returns:
            Dictionary with summary data for Slack
        """
        summary = {
            'report_date': trends.get('report_date'),
            'locations': [],
            'highlights': []
        }

        for location, loc_data in trends.get('locations', {}).items():
            loc_summary = {'name': location, 'products': []}

            for product_name in self.KEY_PRODUCTS[:4]:  # Top 4 products
                products = loc_data.get('products', {})
                if product_name in products:
                    product = products[product_name]
                    current = product['current']
                    loc_summary['products'].append({
                        'name': product_name,
                        'rack_avg': current.get('rack_avg'),
                        'change': product.get('day_change'),
                        'direction': product.get('direction'),
                    })

            summary['locations'].append(loc_summary)

        summary['highlights'] = self._generate_insights(trends)

        return summary


# Backwards compatibility alias
CostProcessor = FuelPriceProcessor
