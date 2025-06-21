import random


from magic_combat import CombatCreature, CombatSimulator


def random_creature(name, controller):
    return CombatCreature(name=name, power=random.randint(1, 5), toughness=random.randint(1, 5), controller=controller)


def simulate_pair(a, b):
    a.blocked_by.append(b)
    b.blocking = a
    sim = CombatSimulator([a], [b])
    return sim.simulate()


def test_combat_independence():
    """CR 109.5: combat damage is assigned and dealt for each pair independently."""
    random.seed(0)
    for _ in range(10):
        a1 = random_creature("a1", "A")
        b1 = random_creature("b1", "B")
        a2 = random_creature("a2", "A")
        b2 = random_creature("b2", "B")

        # combined simulation
        a1.blocked_by.append(b1)
        b1.blocking = a1
        a2.blocked_by.append(b2)
        b2.blocking = a2
        combined = CombatSimulator([a1, a2], [b1, b2])
        comb_res = combined.simulate()

        res1 = simulate_pair(CombatCreature("a1", a1.power, a1.toughness, "A"),
                             CombatCreature("b1", b1.power, b1.toughness, "B"))
        res2 = simulate_pair(CombatCreature("a2", a2.power, a2.toughness, "A"),
                             CombatCreature("b2", b2.power, b2.toughness, "B"))

        expected = {c.name for c in res1.creatures_destroyed + res2.creatures_destroyed}
        assert {c.name for c in comb_res.creatures_destroyed} == expected

