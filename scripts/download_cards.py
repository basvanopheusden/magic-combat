#!/usr/bin/env python
"""Fetch sample creature data from Scryfall and save it as JSON.

This script downloads all "French vanilla" creature cards recognized by
:func:`magic_combat.scryfall_loader.fetch_french_vanilla_cards` and writes the
result to a JSON file. The output path can be specified as an argument, and the
parent directory will be created if it does not already exist.
"""

import argparse
import os

from magic_combat import fetch_french_vanilla_cards, save_cards


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
    args = parser.parse_args()

    cards = fetch_french_vanilla_cards()
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    save_cards(cards, args.output)
    print(f"Saved {len(cards)} cards to {args.output}")


if __name__ == "__main__":
    main()
