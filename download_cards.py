import argparse

from magic_combat.scryfall_loader import fetch_french_vanilla_cards, save_cards


def main() -> None:
    """Download French vanilla creature data and save it to JSON."""
    parser = argparse.ArgumentParser(
        description="Fetch French vanilla creatures from Scryfall and save to JSON"
    )
    parser.add_argument(
        "output",
        help="Path to output JSON file where card data will be written",
    )
    args = parser.parse_args()

    cards = fetch_french_vanilla_cards()
    save_cards(cards, args.output)


if __name__ == "__main__":
    main()
