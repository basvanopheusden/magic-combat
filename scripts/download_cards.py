#!/usr/bin/env python
"""Fetch sample creature data from Scryfall and save it as JSON.

This script downloads all "French vanilla" creature cards recognized by
:func:`magic_combat.scryfall_loader.fetch_french_vanilla_cards` and writes the
result to a JSON file. The output path can be specified as an argument, and the
parent directory will be created if it does not already exist.
"""

import argparse
import os
import sys

# Allow running this script without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from magic_combat import fetch_french_vanilla_cards, save_cards  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download French vanilla creature data from Scryfall"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="data/cards.json",
        help="Location of the JSON file to write",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout for each HTTP request in seconds (default: 10)",
    )
    args = parser.parse_args()

    cards = fetch_french_vanilla_cards(timeout=args.timeout)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    save_cards(cards, args.output)
    print(f"Saved {len(cards)} cards to {args.output}")


if __name__ == "__main__":
    main()
