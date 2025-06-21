"""Damage assignment ordering strategies."""

from typing import List, Tuple

from .creature import CombatCreature


class DamageAssignmentStrategy:
    """Base strategy for ordering blockers when assigning combat damage."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        """Return blockers in the order the attacker will assign damage."""
        return list(blockers)


class MostCreaturesKilledStrategy(DamageAssignmentStrategy):
    """Order blockers so the attacker tries to kill as many as possible."""

    def order_blockers(
        self, attacker: CombatCreature, blockers: List[CombatCreature]
    ) -> List[CombatCreature]:
        power = attacker.effective_power()

        def lethal_cost(blocker: CombatCreature) -> float:
            """Damage needed to remove ``blocker`` from combat."""
            if blocker.indestructible and not (attacker.infect or attacker.wither):
                return float("inf")
            if attacker.deathtouch and not blocker.indestructible:
                return 1
            return blocker.effective_toughness()

        POSITIVE_KEYWORDS = [
            "flying",
            "reach",
            "menace",
            "fear",
            "shadow",
            "horsemanship",
            "skulk",
            "unblockable",
            "vigilance",
            "first_strike",
            "double_strike",
            "deathtouch",
            "trample",
            "lifelink",
            "wither",
            "infect",
            "indestructible",
            "melee",
            "training",
            "battalion",
            "dethrone",
            "intimidate",
            "undying",
            "persist",
        ]

        STACKABLE_KEYWORDS = [
            "bushido",
            "flanking",
            "rampage",
            "exalted_count",
            "battle_cry_count",
            "frenzy",
            "afflict",
        ]

        def value(blocker: CombatCreature) -> float:
            """Heuristic combat value for tie-breaking."""
            positive = sum(1 for attr in POSITIVE_KEYWORDS if getattr(blocker, attr, False))
            positive += sum(1 for attr in STACKABLE_KEYWORDS if getattr(blocker, attr, 0))
            return blocker.power + blocker.toughness + positive / 2

        costs = [lethal_cost(b) for b in blockers]
        values = [value(b) for b in blockers]
        n = len(blockers)

        # Dynamic program over available power to maximize kills then value
        dp: List[Tuple[int, float, List[int]]] = [(0, 0.0, []) for _ in range(power + 1)]
        for i in range(n):
            cost = costs[i]
            if cost == float("inf") or cost > power:
                continue
            int_cost = int(cost)
            for w in range(power, int_cost - 1, -1):
                prev_cnt, prev_val, prev_set = dp[w - int_cost]
                cand_cnt = prev_cnt + 1
                cand_val = prev_val + values[i]
                curr_cnt, curr_val, curr_set = dp[w]
                if cand_cnt > curr_cnt or (cand_cnt == curr_cnt and cand_val > curr_val):
                    dp[w] = (cand_cnt, cand_val, prev_set + [i])

        best = dp[0]
        for w in range(1, power + 1):
            if dp[w][0] > best[0] or (dp[w][0] == best[0] and dp[w][1] > best[1]):
                best = dp[w]

        kill_indices = set(best[2])
        kill_first = [blockers[i] for i in kill_indices]
        kill_first.sort(key=value, reverse=True)
        remaining = [b for idx, b in enumerate(blockers) if idx not in kill_indices]
        remaining.sort(key=value, reverse=True)
        return kill_first + remaining
