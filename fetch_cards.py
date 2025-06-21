"""Convenience script to download card data from Scryfall."""

import argparse
from magic_combat import fetch_french_vanilla_cards, save_cards


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download 'French vanilla' creatures from Scryfall and save as JSON"
    )
    parser.add_argument(
        "output", nargs="?", default="cards.json", help="Path to output JSON file"
    )
    args = parser.parse_args()

    cards = fetch_french_vanilla_cards()
    save_cards(cards, args.output)


if __name__ == "__main__":
    main()
