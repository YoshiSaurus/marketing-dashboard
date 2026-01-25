#!/usr/bin/env python3
"""
Utility to import historical OPIS emails to build price trend baseline.

Usage:
    1. Save OPIS email bodies as .txt files in a directory
    2. Run: python import_history.py /path/to/emails/

    Or import a single file:
    python import_history.py --file email.txt

    Or paste email content interactively:
    python import_history.py --interactive
"""

import argparse
import os
import sys
from pathlib import Path

from src.opis_parser import OPISParser
from src.cost_processor import FuelPriceProcessor


def import_from_file(file_path: str, processor: FuelPriceProcessor, parser: OPISParser) -> bool:
    """Import OPIS data from a single file.

    Args:
        file_path: Path to text file containing OPIS email body
        processor: FuelPriceProcessor instance
        parser: OPISParser instance

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            email_body = f.read()

        # Parse the email
        data = parser.parse(email_body)

        if not data.locations:
            print(f"  Warning: No locations found in {file_path}")
            return False

        # Update history
        processor.update_history(data)

        print(f"  Imported: {data.report_date} - {', '.join(data.locations)} ({len(data.products)} products)")
        return True

    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return False


def import_from_directory(directory: str, processor: FuelPriceProcessor, parser: OPISParser) -> tuple[int, int]:
    """Import all OPIS emails from a directory.

    Args:
        directory: Path to directory containing .txt files
        processor: FuelPriceProcessor instance
        parser: OPISParser instance

    Returns:
        Tuple of (successful_count, failed_count)
    """
    path = Path(directory)

    if not path.exists():
        print(f"Error: Directory not found: {directory}")
        return 0, 0

    # Find all .txt files
    txt_files = sorted(path.glob('*.txt'))

    if not txt_files:
        print(f"No .txt files found in {directory}")
        return 0, 0

    print(f"Found {len(txt_files)} files to import...")
    print()

    successful = 0
    failed = 0

    for file_path in txt_files:
        if import_from_file(str(file_path), processor, parser):
            successful += 1
        else:
            failed += 1

    return successful, failed


def import_interactive(processor: FuelPriceProcessor, parser: OPISParser) -> bool:
    """Import OPIS data by pasting email content interactively.

    Args:
        processor: FuelPriceProcessor instance
        parser: OPISParser instance

    Returns:
        True if successful, False otherwise
    """
    print("Paste the OPIS email body below.")
    print("When done, press Enter twice then Ctrl+D (Unix) or Ctrl+Z (Windows):")
    print("-" * 40)

    try:
        lines = []
        while True:
            try:
                line = input()
                lines.append(line)
            except EOFError:
                break

        email_body = '\n'.join(lines)

        if not email_body.strip():
            print("No content provided.")
            return False

        # Parse the email
        data = parser.parse(email_body)

        if not data.locations:
            print("Warning: No locations found in the provided content.")
            return False

        # Show what was parsed
        print()
        print(f"Parsed data:")
        print(f"  Report Date: {data.report_date}")
        print(f"  Locations: {', '.join(data.locations)}")
        print(f"  Products: {len(data.products)}")

        # Confirm import
        confirm = input("\nImport this data? [Y/n]: ").strip().lower()
        if confirm in ('', 'y', 'yes'):
            processor.update_history(data)
            print("Data imported successfully!")
            return True
        else:
            print("Import cancelled.")
            return False

    except KeyboardInterrupt:
        print("\nCancelled.")
        return False


def show_history_stats(processor: FuelPriceProcessor):
    """Display statistics about the current price history."""
    history = processor._history

    print()
    print("=" * 60)
    print("Price History Statistics")
    print("=" * 60)

    if not history.get('prices'):
        print("No price history data found.")
        return

    print(f"Last Updated: {history.get('last_updated', 'Unknown')}")
    print()

    for location, products in history.get('prices', {}).items():
        print(f"{location}:")
        for product, prices in products.items():
            if prices:
                dates = [p.get('date') for p in prices if p.get('date')]
                if dates:
                    print(f"  {product}:")
                    print(f"    Records: {len(prices)}")
                    print(f"    Date Range: {min(dates)} to {max(dates)}")
        print()


def main():
    parser_args = argparse.ArgumentParser(
        description='Import historical OPIS emails to build price trend baseline.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Import all .txt files from a directory
    python import_history.py /path/to/opis/emails/

    # Import a single file
    python import_history.py --file 2026-01-22-opis.txt

    # Paste email content interactively
    python import_history.py --interactive

    # Show current history statistics
    python import_history.py --stats

    # Use a different history file
    python import_history.py --history my_history.json /path/to/emails/
"""
    )

    parser_args.add_argument(
        'directory',
        nargs='?',
        help='Directory containing OPIS email .txt files'
    )
    parser_args.add_argument(
        '--file', '-f',
        help='Single file to import'
    )
    parser_args.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Paste email content interactively'
    )
    parser_args.add_argument(
        '--history', '-H',
        default='price_history.json',
        help='Price history JSON file (default: price_history.json)'
    )
    parser_args.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show current history statistics'
    )

    args = parser_args.parse_args()

    # Initialize processor and parser
    processor = FuelPriceProcessor(history_file=args.history)
    opis_parser = OPISParser()

    print("=" * 60)
    print("OPIS Historical Data Import")
    print("=" * 60)
    print(f"History file: {args.history}")
    print()

    # Show stats only
    if args.stats:
        show_history_stats(processor)
        return

    # Interactive mode
    if args.interactive:
        success = import_interactive(processor, opis_parser)
        if success:
            show_history_stats(processor)
        return

    # Single file import
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        success = import_from_file(args.file, processor, opis_parser)
        if success:
            show_history_stats(processor)
        return

    # Directory import
    if args.directory:
        successful, failed = import_from_directory(args.directory, processor, opis_parser)

        print()
        print("-" * 40)
        print(f"Import complete: {successful} successful, {failed} failed")

        if successful > 0:
            show_history_stats(processor)
        return

    # No action specified
    parser_args.print_help()


if __name__ == '__main__':
    main()
