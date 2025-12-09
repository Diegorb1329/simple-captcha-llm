#!/usr/bin/env python3
"""SAT Certificate Lookup CLI."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from config import DEFAULT_URL, DEFAULT_INPUT, DEFAULT_OUTPUT
from sat_certificate_lookup import process_rfcs


def main():
    parser = argparse.ArgumentParser(description="Look up SAT certificates for RFCs.")
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_INPUT, help="CSV with RFCs")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT, help="Output directory")
    parser.add_argument("--url", default=DEFAULT_URL, help="SAT page URL")
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: {args.input} not found", file=sys.stderr)
        return 1
    
    try:
        process_rfcs(args.input, args.output, args.url)
        print("Done!")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
