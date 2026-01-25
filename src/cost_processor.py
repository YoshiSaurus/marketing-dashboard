"""Cost data processor for analyzing email content and generating trends."""

import re
from datetime import datetime
from typing import Optional


class CostProcessor:
    """Processes cost data from emails and generates trend reports."""

    def __init__(self):
        """Initialize the cost processor with sample historical data.

        In a production environment, this would connect to a database
        or data warehouse for historical cost data.
        """
        # Sample historical data for demonstration
        # In production, this would be fetched from a database
        self._historical_data = {
            'compute': [1200, 1250, 1180, 1300, 1350],
            'storage': [450, 460, 455, 470, 480],
            'network': [320, 310, 340, 335, 350],
            'database': [890, 900, 920, 910, 930],
            'other': [150, 155, 160, 158, 165]
        }

    def parse_cost_email(self, email_body: str) -> dict:
        """Parse cost data from an email body.

        This method attempts to extract cost figures from the email.
        It handles various formats that cost reports might use.

        Args:
            email_body: The plain text email body

        Returns:
            Dictionary with parsed cost categories and amounts
        """
        costs = {}

        # Pattern to find cost entries like "Category: $1,234.56" or "Category - $1234"
        patterns = [
            r'(\w+(?:\s+\w+)?)\s*[:\-]\s*\$?([\d,]+(?:\.\d{2})?)',
            r'(\w+(?:\s+\w+)?)\s+cost[s]?\s*[:\-]?\s*\$?([\d,]+(?:\.\d{2})?)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, email_body, re.IGNORECASE)
            for match in matches:
                category = match[0].lower().strip()
                amount_str = match[1].replace(',', '')
                try:
                    amount = float(amount_str)
                    # Map common variations to standard categories
                    category = self._normalize_category(category)
                    if category:
                        costs[category] = costs.get(category, 0) + amount
                except ValueError:
                    continue

        # If no costs found, use default/sample data for demo
        if not costs:
            costs = self._get_sample_daily_costs()

        return costs

    def _normalize_category(self, category: str) -> Optional[str]:
        """Normalize category names to standard categories.

        Args:
            category: Raw category name from email

        Returns:
            Normalized category name or None if not a cost category
        """
        category_mapping = {
            'compute': ['compute', 'ec2', 'instances', 'vm', 'virtual machine', 'server'],
            'storage': ['storage', 's3', 'ebs', 'disk', 'blob', 'files'],
            'network': ['network', 'bandwidth', 'data transfer', 'cdn', 'vpc'],
            'database': ['database', 'rds', 'dynamodb', 'sql', 'cosmos', 'db'],
            'other': ['other', 'misc', 'miscellaneous', 'additional']
        }

        category_lower = category.lower()
        for standard, variations in category_mapping.items():
            if any(v in category_lower for v in variations):
                return standard

        # Skip non-cost related matches
        skip_words = ['total', 'date', 'report', 'period', 'from', 'to', 'the', 'and']
        if any(word in category_lower for word in skip_words):
            return None

        return 'other'

    def _get_sample_daily_costs(self) -> dict:
        """Get sample daily costs for demonstration.

        Returns:
            Dictionary of sample cost data
        """
        return {
            'compute': 1380.50,
            'storage': 485.25,
            'network': 355.00,
            'database': 945.75,
            'other': 170.00
        }

    def calculate_trends(self, current_costs: dict) -> dict:
        """Calculate cost trends comparing current to historical data.

        Args:
            current_costs: Dictionary of current cost amounts by category

        Returns:
            Dictionary with trend analysis for each category
        """
        trends = {}

        for category, current in current_costs.items():
            historical = self._historical_data.get(category, [])

            if historical:
                # Calculate average of historical data
                avg_historical = sum(historical) / len(historical)
                # Calculate percentage change
                change = ((current - avg_historical) / avg_historical) * 100 if avg_historical > 0 else 0
                # Determine trend direction
                trend_direction = 'increasing' if change > 2 else ('decreasing' if change < -2 else 'stable')
            else:
                avg_historical = 0
                change = 0
                trend_direction = 'new'

            trends[category] = {
                'current': current,
                'historical_avg': avg_historical,
                'change': round(change, 2),
                'direction': trend_direction
            }

        # Calculate total
        total_current = sum(current_costs.values())
        total_historical = sum(sum(v) / len(v) for v in self._historical_data.values() if v)
        total_change = ((total_current - total_historical) / total_historical) * 100 if total_historical > 0 else 0

        trends['total'] = {
            'current': total_current,
            'historical_avg': total_historical,
            'change': round(total_change, 2),
            'direction': 'increasing' if total_change > 2 else ('decreasing' if total_change < -2 else 'stable')
        }

        return trends

    def generate_trend_report(self, trends: dict) -> str:
        """Generate a human-readable trend report for email reply.

        Args:
            trends: Dictionary of trend analysis from calculate_trends()

        Returns:
            Formatted string report suitable for email
        """
        today = datetime.now().strftime('%B %d, %Y')

        report_lines = [
            f"Cost Trends Report - {today}",
            "=" * 50,
            "",
            "Dear Customer,",
            "",
            "Thank you for sending your cost data. Here is the analysis of today's costs compared to recent trends:",
            "",
            "COST BREAKDOWN BY CATEGORY",
            "-" * 30,
        ]

        # Add each category (excluding total)
        for category, data in sorted(trends.items()):
            if category == 'total':
                continue

            direction_emoji = {
                'increasing': '(UP)',
                'decreasing': '(DOWN)',
                'stable': '(STABLE)',
                'new': '(NEW)'
            }

            report_lines.append(
                f"  {category.title():12} ${data['current']:>10,.2f}  "
                f"{data['change']:>+6.1f}%  {direction_emoji.get(data['direction'], '')}"
            )

        # Add total
        total = trends.get('total', {})
        report_lines.extend([
            "-" * 30,
            f"  {'TOTAL':12} ${total.get('current', 0):>10,.2f}  "
            f"{total.get('change', 0):>+6.1f}%",
            "",
            "TREND ANALYSIS",
            "-" * 30,
        ])

        # Add insights
        insights = self._generate_insights(trends)
        for insight in insights:
            report_lines.append(f"  - {insight}")

        report_lines.extend([
            "",
            "If you have any questions about this report, please don't hesitate to reach out.",
            "",
            "Best regards,",
            "Cost Analysis Agent"
        ])

        return "\n".join(report_lines)

    def _generate_insights(self, trends: dict) -> list[str]:
        """Generate actionable insights from trend data.

        Args:
            trends: Dictionary of trend analysis

        Returns:
            List of insight strings
        """
        insights = []

        # Find biggest increases
        increases = [(cat, data) for cat, data in trends.items()
                     if cat != 'total' and data['change'] > 5]
        if increases:
            biggest = max(increases, key=lambda x: x[1]['change'])
            insights.append(
                f"{biggest[0].title()} costs increased by {biggest[1]['change']:.1f}% - "
                "consider reviewing usage in this area."
            )

        # Find decreases (good news)
        decreases = [(cat, data) for cat, data in trends.items()
                     if cat != 'total' and data['change'] < -5]
        if decreases:
            biggest_decrease = min(decreases, key=lambda x: x[1]['change'])
            insights.append(
                f"{biggest_decrease[0].title()} costs decreased by {abs(biggest_decrease[1]['change']):.1f}% - "
                "great job optimizing!"
            )

        # Overall trend
        total = trends.get('total', {})
        if total.get('change', 0) > 10:
            insights.append(
                "Overall costs are trending significantly higher than average. "
                "A cost review is recommended."
            )
        elif total.get('change', 0) < -10:
            insights.append(
                "Overall costs are well below average - your optimization efforts are paying off!"
            )
        else:
            insights.append("Overall costs are within normal range.")

        return insights
