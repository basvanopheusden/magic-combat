#!/usr/bin/env python
"""Generate and resolve random combat scenarios."""

import argparse
import os
import random
import copy
from typing import Dict, List

import numpy as np

from magic_combat import (
    cards_to_creatures,
    card_to_creature,
    load_cards,
    save_cards,
    fetch_french_vanilla_cards,
    compute_card_statistics,
    generate_random_creature,
    assign_random_counters,
    assign_random_tapped,
    decide_optimal_blocks,
    decide_simple_blocks,
    CombatSimulator,
    GameState,
    PlayerState,
)
from magic_combat.damage import _blocker_value

# Ability name mappings for pretty printing
_BOOL_ABILITIES = {
    "flying": "Flying",
    "reach": "Reach",
    "menace": "Menace",
    "fear": "Fear",
    "shadow": "Shadow",
    "horsemanship": "Horsemanship",
    "skulk": "Skulk",
    "unblockable": "Unblockable",
    "daunt": "Daunt",
    "vigilance": "Vigilance",
    "first_strike": "First strike",
    "double_strike": "Double strike",
    "deathtouch": "Deathtouch",
    "trample": "Trample",
    "lifelink": "Lifelink",
    "wither": "Wither",
    "infect": "Infect",
    "indestructible": "Indestructible",
    "melee": "Melee",
    "training": "Training",
    "mentor": "Mentor",
    "battalion": "Battalion",
    "dethrone": "Dethrone",
    "undying": "Undying",
    "persist": "Persist",
    "intimidate": "Intimidate",
    "defender": "Defender",
    "provoke": "Provoke",
}

_INT_ABILITIES = {
    "toxic": "Toxic",
    "bushido": "Bushido",
    "flanking": "Flanking",
    "rampage": "Rampage",
    "exalted_count": "Exalted",
    "battle_cry_count": "Battle cry",
    "frenzy": "Frenzy",
    "afflict": "Afflict",
}


def describe_abilities(creature) -> str:
    """Return a comma-separated string of the creature's keyword abilities."""
    parts: List[str] = []
    for attr, name in _BOOL_ABILITIES.items():
        if getattr(creature, attr, False):
            parts.append(name)
    for attr, name in _INT_ABILITIES.items():
        val = getattr(creature, attr, 0)
        if val:
            parts.append(f"{name} {val}")
    if creature.protection_colors:
        colors = ", ".join(c.name.capitalize() for c in creature.protection_colors)
        parts.append(f"Protection from {colors}")
    if creature.artifact:
        parts.append("Artifact")
    return ", ".join(parts) if parts else "none"


def summarize_creature(creature) -> str:
    """Return a readable one-line summary of ``creature``."""
    extra: List[str] = []
    if creature.plus1_counters:
        extra.append(f"+1/+1 x{creature.plus1_counters}")
    if creature.minus1_counters:
        extra.append(f"-1/-1 x{creature.minus1_counters}")
    if creature.damage_marked:
        extra.append(f"{creature.damage_marked} dmg")
    if creature.tapped:
        extra.append("tapped")
    extras = f" [{' ,'.join(extra)}]" if extra else ""
    return f"{creature}{extras} -- {describe_abilities(creature)}"


def print_player_state(label: str, ps: PlayerState, destroyed: List) -> None:
    """Display life total and surviving creatures for a player."""
    print(f"{label}: {ps.life} life, {ps.poison} poison")
    survivors = [c for c in ps.creatures if c not in destroyed]
    if survivors:
        for cr in survivors:
            print(f"  {summarize_creature(cr)}")
    else:
        print("  no creatures")


def ensure_cards(path: str) -> List[dict]:
    """Load card data, downloading it if necessary."""
    if not os.path.exists(path):
        print(f"Downloading card data to {path}...")
        try:
            cards = fetch_french_vanilla_cards()
        except Exception as exc:
            raise SystemExit(f"Failed to download card data: {exc}")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        save_cards(cards, path)
    return load_cards(path)


def build_value_map(cards: List[dict]) -> Dict[int, float]:
    """Return a mapping of card index to combat value.

    Cards with invalid stats (e.g. ``"*"`` toughness) are skipped.
    """
    values: Dict[int, float] = {}
    for idx, card in enumerate(cards):
        try:
            creature = card_to_creature(card, "A")
        except ValueError as exc:  # toughness/power may be invalid
            print(f"Skipping {card.get('name', '?')}: {exc}")
            continue
        values[idx] = _blocker_value(creature)
    if not values:
        raise ValueError("No usable creatures found in card data")
    return values


def sample_balanced(
    cards: List[dict], values: Dict[int, float], n_att: int, n_blk: int
) -> tuple[List[int], List[int]]:
    """Select creatures for each side with roughly equal total value.

    If no sufficiently balanced pairing is found after many attempts, a
    ``ValueError`` is raised so the caller can try different creature
    counts.  This prevents wildly unbalanced scenarios such as a single
    small attacker facing an entire army of blockers.
    """

    idxs = list(values.keys())
    if n_att + n_blk > len(idxs):
        raise ValueError("Not enough cards to sample from")

    best: tuple[list[int], list[int]] | None = None
    best_diff = float("inf")

    for _ in range(1000):
        att_idx = random.sample(idxs, n_att)
        remaining = [i for i in idxs if i not in att_idx]
        blk_idx = random.sample(remaining, n_blk)

        att_val = sum(values[i] for i in att_idx)
        blk_val = sum(values[i] for i in blk_idx)
        avg = (att_val + blk_val) / 2 or 1
        diff = abs(att_val - blk_val) / avg

        if diff < best_diff:
            best = (att_idx, blk_idx)
            best_diff = diff

        if diff <= 0.25:
            return att_idx, blk_idx

    # No sufficiently balanced selection found
    if best is None:
        raise ValueError("Failed to sample creatures")
    raise ValueError("Unable to generate balanced creature sets")


def generate_balanced_creatures(
    stats: Dict[str, object], n_att: int, n_blk: int
) -> tuple[List, List]:
    """Generate two sets of creatures with roughly equal value."""

    best: tuple[list, list] | None = None
    best_diff = float("inf")

    for _ in range(1000):
        attackers = [generate_random_creature(stats, controller="A") for _ in range(n_att)]
        blockers = [generate_random_creature(stats, controller="B") for _ in range(n_blk)]

        att_val = sum(_blocker_value(c) for c in attackers)
        blk_val = sum(_blocker_value(c) for c in blockers)
        avg = (att_val + blk_val) / 2 or 1
        diff = abs(att_val - blk_val) / avg

        if diff < best_diff:
            best = (attackers, blockers)
            best_diff = diff

        if diff <= 0.25:
            return attackers, blockers

    if best is None:
        raise ValueError("Failed to generate creatures")
    raise ValueError("Unable to generate balanced creature sets")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate random combat scenarios"
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=10,
        help="Number of scenarios to generate",
    )
    parser.add_argument(
        "--cards",
        default="data/cards.json",
        help="Path to card data JSON",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed controlling sampling",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=int(1e6),
        help="Maximum combat simulations per scenario",
    )
    parser.add_argument(
        "--generated-cards",
        action="store_true",
        help="Use randomly generated creatures instead of real cards",
    )
    parser.add_argument(
        "--unique-optimal",
        action="store_true",
        help="Skip scenarios without a single optimal blocking set",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    cards = ensure_cards(args.cards)
    values = build_value_map(cards)
    stats = compute_card_statistics(cards) if args.generated_cards else None
    valid_len = len(values)

    for i in range(args.iterations):
        attempts = 0
        while True:
            attempts += 1
            if attempts > 100:
                raise RuntimeError("Unable to generate valid scenario")

            n_atk = int(np.random.geometric(1 / 2.5))
            n_blk = int(np.random.geometric(1 / 2.5))
            n_atk = max(1, min(n_atk, valid_len // 2))
            n_blk = max(1, min(n_blk, valid_len // 2))

            try:
                if args.generated_cards:
                    attackers, blockers = generate_balanced_creatures(stats, n_atk, n_blk)
                else:
                    atk_idx, blk_idx = sample_balanced(cards, values, n_atk, n_blk)
                    attackers = cards_to_creatures((cards[j] for j in atk_idx), "A")
                    blockers = cards_to_creatures((cards[j] for j in blk_idx), "B")
            except ValueError:
                continue

            assign_random_counters(attackers + blockers)
            assign_random_tapped(blockers)

            poison_relevant = any(c.infect or c.toxic for c in attackers + blockers)

            state = GameState(
                players={
                    "A": PlayerState(
                        life=random.randint(1, 20),
                        creatures=attackers,
                        poison=random.randint(0, 9) if poison_relevant else 0,
                    ),
                    "B": PlayerState(
                        life=random.randint(1, 20),
                        creatures=blockers,
                        poison=random.randint(0, 9) if poison_relevant else 0,
                    ),
                }
            )

            provoke_map = {
                atk: random.choice(blockers)
                for atk in attackers
                if atk.provoke
            }
            for blk in provoke_map.values():
                blk.tapped = False

            mentor_map = {}
            for mentor in attackers:
                if mentor.mentor:
                    targets = [
                        c
                        for c in attackers
                        if c is not mentor and c.effective_power() < mentor.effective_power()
                    ]
                    if targets:
                        mentor_map[mentor] = random.choice(targets)

            # Compute simple heuristic assignment on copies
            simple_atk = copy.deepcopy(attackers)
            simple_blk = copy.deepcopy(blockers)
            simple_state = copy.deepcopy(state)
            try:
                decide_simple_blocks(
                    simple_atk,
                    simple_blk,
                    game_state=simple_state,
                    provoke_map=provoke_map,
                )
                sim_check = CombatSimulator(simple_atk, simple_blk, game_state=simple_state)
                sim_check.validate_blocking()
                atk_map = {id(a): i for i, a in enumerate(simple_atk)}
                simple_assignment = tuple(
                    atk_map.get(id(b.blocking), None) for b in simple_blk
                )
            except ValueError:
                simple_assignment = None

            try:
                iters, opt_count = decide_optimal_blocks(
                    attackers,
                    blockers,
                    game_state=state,
                    provoke_map=provoke_map,
                    max_iterations=args.max_iterations,
                )
                if args.unique_optimal and opt_count != 1:
                    print(
                        f"Skipping scenario {i+1}_{attempts}: {opt_count} optimal assignments"
                    )
                    continue
            except (ValueError, RuntimeError):
                continue

            opt_map = {id(a): i for i, a in enumerate(attackers)}
            optimal_assignment = tuple(
                opt_map.get(id(b.blocking), None) for b in blockers
            )
            if (
                simple_assignment is not None
                and simple_assignment == optimal_assignment
            ):
                print(f'Skipping scenario {i+1}_{attempts}: too easy')
                continue

            start_state = copy.deepcopy(state)
            sim = CombatSimulator(
                attackers,
                blockers,
                game_state=state,
                provoke_map=provoke_map,
                mentor_map=mentor_map,
            )
            result = sim.simulate()
            break

        print(f"\n=== Scenario {i+1} ===")
        print("Starting life totals:")
        for p in ["A", "B"]:
            ps = start_state.players[p]
            print(f"  Player {p}: {ps.life} life, {ps.poison} poison")

        print("Attackers:")
        for atk in start_state.players["A"].creatures:
            print(f"  {summarize_creature(atk)}, {_blocker_value(atk)}")
        print("Blockers:")
        for blk in start_state.players["B"].creatures:
            print(f"  {summarize_creature(blk)}, {_blocker_value(blk)}")

        prov_map_display = {a.name: b.name for a, b in provoke_map.items()} if provoke_map else None
        mentor_map_display = {m.name: t.name for m, t in mentor_map.items()} if mentor_map else None

        print("Block assignments:")
        for atk in start_state.players["A"].creatures:
            blocks = ", ".join(b.name for b in atk.blocked_by) or "unblocked"
            print(f"  {atk.name} -> {blocks}")
        for blk in start_state.players["B"].creatures:
            target = blk.blocking.name if blk.blocking else "none"
            print(f"  {blk.name} -> {target}")
        if prov_map_display:
            print("Provoke targets:", prov_map_display)
        if mentor_map_display:
            print("Mentor targets:", mentor_map_display)

        print("Outcome:")
        print(result)

        print("Final state:")
        for p in ["A", "B"]:
            print_player_state(f"Player {p}", state.players[p], result.creatures_destroyed)
        if result.players_lost:
            print("Players lost:", ", ".join(result.players_lost))
        print()


if __name__ == "__main__":
    main()
