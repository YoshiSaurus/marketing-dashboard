#!/usr/bin/env python3
"""Test script to verify OPIS email parsing without Gmail integration."""

from src.opis_parser import OPISParser
from src.cost_processor import FuelPriceProcessor
import json

# Sample OPIS email body (from the provided example)
SAMPLE_OPIS_EMAIL = """
Account #137517

To align the following data, change the font size to 9 in Courier New.

AMARILLO, TX                                           2026-01-23 09:00:06 EST
                   **OPIS GROSS CONV. CLEAR PRICES**                   9.0 RVP
                                                                Move
             Terms  Unl     Move   Mid     Move   Pre     Move  Date  Time
Valero     b 1-10  208.03  - 1.43  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        b 1-10  211.62  - 3.50  -- --   -- -- 265.96  - 3.50 01/22 18:00
Valero     u N-10  230.78  - 2.54  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        u N-10  233.60  - 3.50  -- --   -- -- 286.60  - 3.50 01/22 18:00
LOW RACK           208.03          -- --         265.96
HIGH RACK          233.60          -- --         286.60
RACK AVG           221.01          -- --         276.28
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB AMARILLO      174.89          -- --         183.14
BRD LOW RACK       208.03          -- --         265.96
BRD HIGH RACK      211.62          -- --         265.96
BRD RACK AVG       209.83          -- --         265.96
UBD LOW RACK       230.78          -- --         286.60
UBD HIGH RACK      233.60          -- --         286.60
UBD RACK AVG       232.19          -- --         286.60
CONT AVG-01/22     223.75          -- --         279.78
CONT LOW-01/22     209.46          -- --         269.46
CONT HIGH-01/22    237.10          -- --         290.10

AMARILLO, TX
LOW RETAIL              215.77
AVG RETAIL              235.05
LOW RETAIL EX-TAX       176.89
AVG RETAIL EX-TAX       196.18

AMARILLO, TX                                           2026-01-23 09:00:06 EST
                **OPIS GROSS CBOB ETHANOL(10%) PRICES**                9.0 RVP
                                                                Move
             Terms  Unl     Move   Mid     Move   Pre     Move  Date  Time
Valero     b 1-10  171.67  - 2.44 186.62  - 2.34 227.32  - 2.45 01/22 18:00
PSX        b 1-10  172.32  - 2.10 188.48  - 2.10 226.66  - 2.10 01/22 18:00
PSX        u N-10  175.20  - 2.90 191.20  - 2.90 228.20  - 2.90 01/22 18:00
Valero     u N-10  175.28  - 2.54 191.28  - 2.54 228.28  - 2.54 01/22 18:00
Cenex      b 1-10  176.42  - 3.50  -- --   -- -- 232.75  - 3.30 01/22 18:00
DKTS       b 1-10  176.48  - 3.15  -- --   -- -- 227.23  - 3.15 01/22 18:00
XOM        b 125-3 187.02  - 3.18  -- --   -- -- 247.27  - 3.18 01/22 19:00
Chevron    b 1-10  187.40  - 3.30 206.30  - 3.30 244.00  - 3.30 01/22 18:00
LOW RACK           171.67         186.62         226.66
HIGH RACK          187.40         206.30         247.27
RACK AVG           177.72         192.78         232.71
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB AMARILLO      175.32          -- --          -- --
BRD LOW RACK       171.67         186.62         226.66
BRD HIGH RACK      187.40         206.30         247.27
BRD RACK AVG       178.55         193.80         234.21
UBD LOW RACK       175.20         191.20         228.20
UBD HIGH RACK      175.28         191.28         228.28
UBD RACK AVG       175.24         191.24         228.24
CONT AVG-01/22     180.62         195.41         235.59
CONT LOW-01/22     174.11         188.96         228.76
CONT HIGH-01/22    190.70         209.60         250.45

AMARILLO, TX                                           2026-01-23 09:00:06 EST
           **OPIS GROSS ULTRA LOW SULFUR DISTILLATE PRICES**
                                                                Move
             Terms  No.2    Move   No.1    Move   Pre     Move  Date  Time
Valero     b 1-10  227.33  -  .29  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        b 1-10  228.62  - 2.60  -- --   -- --  -- --   -- -- 01/22 18:00
DKTS       b 1-10  229.91  -  .98  -- --   -- --  -- --   -- -- 01/22 18:00
Valero     u N-10  236.20  - 4.37  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        u N-10  241.60  - 3.40  -- --   -- --  -- --   -- -- 01/22 18:00
LOW RACK           227.33          -- --          -- --
HIGH RACK          241.60          -- --          -- --
RACK AVG           232.73          -- --          -- --
OPIS GROUP 3 SPOT MEAN - 01/22
 FOB MAGELLAN      209.805         -- --          -- --
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB AMARILLO      217.95          -- --          -- --
BRD LOW RACK       227.33          -- --          -- --
BRD HIGH RACK      229.91          -- --          -- --
BRD RACK AVG       228.62          -- --          -- --
UBD LOW RACK       236.20          -- --          -- --
UBD HIGH RACK      241.60          -- --          -- --
UBD RACK AVG       238.90          -- --          -- --
CONT AVG-01/22     235.06          -- --          -- --
CONT LOW-01/22     227.62          -- --          -- --
CONT HIGH-01/22    245.00          -- --          -- --

AMARILLO, TX                                           2026-01-23 09:00:06 EST
       **OPIS GROSS ULTRA LOW SULFUR RED DYE DISTILLATE PRICES**
                                                                Move
             Terms  No.2    Move   No.1    Move   Pre     Move  Date  Time
Valero     b 1-10  227.69  -  .28  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        b 1-10  229.13  - 2.60  -- --   -- --  -- --   -- -- 01/22 18:00
Valero     u N-10  236.55  - 4.37  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        u N-10  242.10  - 3.40  -- --   -- --  -- --   -- -- 01/22 18:00
LOW RACK           227.69          -- --          -- --
HIGH RACK          242.10          -- --          -- --
RACK AVG           233.87          -- --          -- --
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB AMARILLO      218.30          -- --          -- --
BRD LOW RACK       227.69          -- --          -- --
BRD HIGH RACK      229.13          -- --          -- --
BRD RACK AVG       228.41          -- --          -- --
UBD LOW RACK       236.55          -- --          -- --
UBD HIGH RACK      242.10          -- --          -- --
UBD RACK AVG       239.33          -- --          -- --
CONT AVG-01/22     236.53          -- --          -- --
CONT LOW-01/22     227.97          -- --          -- --
CONT HIGH-01/22    245.50          -- --          -- --

LUBBOCK, TX                                            2026-01-23 09:00:06 EST
                   **OPIS GROSS CONV. CLEAR PRICES**                   9.0 RVP
                                                                Move
             Terms  Unl     Move   Mid     Move   Pre     Move  Date  Time
PSX        b 1-10  210.72  - 3.50  -- --   -- -- 264.25  - 3.50 01/22 18:00
Valero     b 1-10  211.38  - 2.90  -- --   -- --  -- --   -- -- 01/22 18:00
Valero     u N-10  241.28  - 2.59  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        u N-10  245.10  - 3.50  -- --   -- -- 298.10  - 3.50 01/22 18:00
LOW RACK           210.72          -- --         264.25
HIGH RACK          245.10          -- --         298.10
RACK AVG           227.12          -- --         281.18
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB LUBBOCK       170.28          -- --         178.53
BRD LOW RACK       210.72          -- --         264.25
BRD HIGH RACK      211.38          -- --         264.25
BRD RACK AVG       211.05          -- --         264.25
UBD LOW RACK       241.28          -- --         298.10
UBD HIGH RACK      245.10          -- --         298.10
UBD RACK AVG       243.19          -- --         298.10
CONT AVG-01/22     230.24          -- --         284.68
CONT LOW-01/22     214.22          -- --         267.75
CONT HIGH-01/22    248.60          -- --         301.60

LUBBOCK, TX
LOW RETAIL              211.77
AVG RETAIL              226.43
LOW RETAIL EX-TAX       172.89
AVG RETAIL EX-TAX       187.56

LUBBOCK, TX                                            2026-01-23 09:00:06 EST
                **OPIS GROSS CBOB ETHANOL(10%) PRICES**                9.0 RVP
                                                                Move
             Terms  Unl     Move   Mid     Move   Pre     Move  Date  Time
DKTS       b 1-10  174.15  - 2.88  -- --   -- -- 206.15  - 2.88 01/22 18:00
PSX        b 1-10  174.34  - 2.40 190.50  - 2.40 227.88  - 2.40 01/22 18:00
Valero     b 1-10  174.46  - 2.90 190.63  - 2.84 217.24  - 2.90 01/22 18:00
PSX        u N-10  175.20  - 2.90 188.95  - 2.90 228.20  - 2.90 01/22 18:00
Valero     u N-10  175.28  - 2.59 189.18  - 2.69 228.43  - 2.69 01/22 18:00
LOW RACK           174.15         188.95         206.15
HIGH RACK          175.28         190.63         228.43
RACK AVG           174.69         189.82         221.58
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB LUBBOCK       170.70          -- --          -- --
BRD LOW RACK       174.15         190.50         206.15
BRD HIGH RACK      174.46         190.63         227.88
BRD RACK AVG       174.32         190.57         217.09
UBD LOW RACK       175.20         188.95         228.20
UBD HIGH RACK      175.28         189.18         228.43
UBD RACK AVG       175.24         189.07         228.32
CONT AVG-01/22     177.42         192.52         224.33
CONT LOW-01/22     176.74         191.85         209.03
CONT HIGH-01/22    178.10         193.47         231.12

LUBBOCK, TX                                            2026-01-23 09:00:06 EST
           **OPIS GROSS ULTRA LOW SULFUR DISTILLATE PRICES**
                                                                Move
             Terms  No.2    Move   No.1    Move   Pre     Move  Date  Time
Valero     b 1-10  227.74  - 3.39  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        b 1-10  228.75  - 2.50  -- --   -- --  -- --   -- -- 01/22 18:00
Valero     u N-10  236.83  - 4.62  -- --   -- --  -- --   -- -- 01/22 18:00
PSX        u N-10  241.60  - 3.40  -- --   -- --  -- --   -- -- 01/22 18:00
LOW RACK           227.74          -- --          -- --
HIGH RACK          241.60          -- --          -- --
RACK AVG           233.73          -- --          -- --
OPIS GROUP 3 SPOT MEAN - 01/22
 FOB MAGELLAN      209.805         -- --          -- --
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB LUBBOCK       213.31          -- --          -- --
BRD LOW RACK       227.74          -- --          -- --
BRD HIGH RACK      228.75          -- --          -- --
BRD RACK AVG       228.25          -- --          -- --
UBD LOW RACK       236.83          -- --          -- --
UBD HIGH RACK      241.60          -- --          -- --
UBD RACK AVG       239.22          -- --          -- --
CONT AVG-01/22     237.21          -- --          -- --
CONT LOW-01/22     231.13          -- --          -- --
CONT HIGH-01/22    245.00          -- --          -- --

LUBBOCK, TX                                            2026-01-23 09:00:06 EST
       **OPIS GROSS ULTRA LOW SULFUR RED DYE DISTILLATE PRICES**
                                                                Move
             Terms  No.2    Move   No.1    Move   Pre     Move  Date  Time
Valero     b 1-10  228.09  - 3.39  -- --   -- --  -- --   -- -- 01/22 18:00
Valero     u N-10  237.18  - 4.62  -- --   -- --  -- --   -- -- 01/22 18:00
LOW RACK           228.09          -- --          -- --
HIGH RACK          237.18          -- --          -- --
RACK AVG           232.64          -- --          -- --
OPIS GROUP 3 DELIVERED SPOT (SRI)
 FOB LUBBOCK       213.66          -- --          -- --
BRD LOW RACK       228.09          -- --          -- --
BRD HIGH RACK      228.09          -- --          -- --
BRD RACK AVG       228.09          -- --          -- --
UBD LOW RACK       237.18          -- --          -- --
UBD HIGH RACK      237.18          -- --          -- --
UBD RACK AVG       237.18          -- --          -- --
CONT AVG-01/22     236.64          -- --          -- --
CONT LOW-01/22     231.48          -- --          -- --
CONT HIGH-01/22    241.80          -- --          -- --
Copyright, Oil Price Information Service
"""


def test_parser():
    """Test the OPIS parser with sample data."""
    print("=" * 60)
    print("OPIS Parser Test")
    print("=" * 60)
    print()

    # Initialize parser
    parser = OPISParser()

    # Parse the sample email
    print("Parsing sample OPIS email...")
    data = parser.parse(SAMPLE_OPIS_EMAIL)

    # Display results
    print(f"\n{'PARSING RESULTS':=^60}")
    print(f"Account Number: {data.account_number}")
    print(f"Report Date: {data.report_date}")
    print(f"Locations Found: {data.locations}")
    print(f"Product Sections: {len(data.products)}")
    print(f"Retail Price Sections: {len(data.retail_prices)}")

    # Show products by location
    print(f"\n{'PRODUCTS BY LOCATION':=^60}")
    for location in data.locations:
        print(f"\n  {location}:")
        location_products = [p for p in data.products if p.location == location]
        for product in location_products:
            display_name = parser.PRODUCT_DISPLAY_NAMES.get(product.product_type, product.product_type)
            rack = product.rack_prices.get('primary')
            if rack and rack.avg:
                print(f"    - {display_name}: Rack Avg = {rack.avg:.2f} cpg")

    # Show retail prices
    print(f"\n{'RETAIL PRICES':=^60}")
    for retail in data.retail_prices:
        print(f"\n  {retail.location}:")
        print(f"    Avg Retail: {retail.avg_retail} cpg")
        print(f"    Low Retail: {retail.low_retail} cpg")
        print(f"    Avg Ex-Tax: {retail.avg_retail_ex_tax} cpg")

    # Get summary
    print(f"\n{'SUMMARY DATA':=^60}")
    summary = parser.get_summary(data)
    print(json.dumps(summary, indent=2, default=str))

    return data


def test_processor():
    """Test the fuel price processor with sample data."""
    print("\n")
    print("=" * 60)
    print("Fuel Price Processor Test")
    print("=" * 60)
    print()

    # Initialize processor (uses test history file)
    processor = FuelPriceProcessor(history_file='test_price_history.json')

    # Parse and process
    print("Processing OPIS data...")
    opis_data = processor.parse_opis_email(SAMPLE_OPIS_EMAIL)

    # Calculate trends (will show N/A for first run since no history)
    trends = processor.calculate_trends(opis_data)

    # Update history
    processor.update_history(opis_data)
    print("Price history updated.")

    # Generate report
    print(f"\n{'TREND REPORT':=^60}")
    report = processor.generate_trend_report(trends)
    print(report)

    # Generate Slack summary
    print(f"\n{'SLACK SUMMARY':=^60}")
    slack_summary = processor.generate_slack_summary(trends)
    print(json.dumps(slack_summary, indent=2, default=str))

    return trends


if __name__ == '__main__':
    # Run tests
    data = test_parser()
    trends = test_processor()

    print("\n")
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nThe parser successfully extracted:")
    print(f"  - {len(data.locations)} locations")
    print(f"  - {len(data.products)} product sections")
    print(f"  - {len(data.retail_prices)} retail price sections")
    print("\nA test history file was created: test_price_history.json")
    print("You can delete it after testing.")
