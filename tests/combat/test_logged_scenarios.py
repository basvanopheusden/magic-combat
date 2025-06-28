import pytest

from magic_combat import (
    CombatCreature,
    CombatSimulator,
    GameState,
    PlayerState,
    decide_optimal_blocks,
)
from magic_combat.creature import Color


def test_logged_scenario_17():
    """CR 702.108a: A creature with horsemanship can't be blocked except by creatures with horsemanship."""
    A, B = "A", "B"
    lu_meng = CombatCreature("Lu Meng, Wu General", 4, 4, A, horsemanship=True)
    recluse = CombatCreature("Kessig Recluse", 2, 3, A, reach=True, deathtouch=True)
    spider = CombatCreature("Sentinel Spider", 4, 4, B, reach=True, vigilance=True)
    wall = CombatCreature("Glacial Wall", 0, 7, B, defender=True)
    state = GameState(
        players={
            A: PlayerState(life=8, creatures=[lu_meng, recluse]),
            B: PlayerState(life=1, creatures=[spider, wall]),
        }
    )
    decide_optimal_blocks([lu_meng, recluse], [spider, wall], game_state=state)
    assert spider.blocking is None
    assert wall.blocking is None
    sim = CombatSimulator([lu_meng, recluse], [spider, wall], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 6
    assert "B" in result.players_lost


def test_logged_scenario_18():
    """CR 702.110b: A creature with menace must be blocked by two or more creatures."""
    A, B = "A", "B"
    runner = CombatCreature("Viashino Runner", 3, 2, A, menace=True)
    creeper = CombatCreature("Kederekt Creeper", 2, 3, A, menace=True, deathtouch=True)
    sentinel = CombatCreature("Sun Sentinel", 2, 2, A, vigilance=True)
    zetalpa = CombatCreature(
        "Zetalpa, Primal Dawn",
        4,
        8,
        B,
        flying=True,
        vigilance=True,
        double_strike=True,
        trample=True,
        indestructible=True,
    )
    state = GameState(
        players={
            A: PlayerState(life=16, creatures=[runner, creeper, sentinel]),
            B: PlayerState(life=12, creatures=[zetalpa]),
        }
    )
    decide_optimal_blocks([runner, creeper, sentinel], [zetalpa], game_state=state)
    assert zetalpa.blocking is sentinel
    sim = CombatSimulator([runner, creeper, sentinel], [zetalpa], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 5
    assert result.creatures_destroyed == [sentinel]


def test_logged_scenario_19():
    """CR 702.36a: Fear allows only black or artifact creatures to block this creature."""
    A, B = "A", "B"
    aven = CombatCreature("Aven Skirmisher", 1, 1, A, flying=True)
    boggart = CombatCreature("Prickly Boggart", 1, 1, A, fear=True)
    griffin = CombatCreature("Griffin Sentinel", 1, 3, A, flying=True, vigilance=True)
    sea = CombatCreature("Sea Eagle", 1, 1, B, flying=True)
    airship = CombatCreature("Talas Air Ship", 3, 2, B, flying=True)
    state = GameState(
        players={
            A: PlayerState(life=1, creatures=[aven, boggart, griffin]),
            B: PlayerState(life=11, creatures=[sea, airship]),
        }
    )
    decide_optimal_blocks([aven, boggart, griffin], [sea, airship], game_state=state)
    assert sea.blocking is aven
    assert airship.blocking is griffin
    sim = CombatSimulator([aven, boggart, griffin], [sea, airship], game_state=state)
    result = sim.simulate()
    dead = {c.name for c in result.creatures_destroyed}
    assert dead == {"Aven Skirmisher", "Griffin Sentinel", "Sea Eagle"}
    assert result.damage_to_players["B"] == 1


def test_logged_scenario_20():
    """CR 702.90a: Damage from a creature with infect is dealt as -1/-1 counters and poison counters."""
    A, B = "A", "B"
    billy = CombatCreature("Kithkin Billyrider", 1, 3, A, double_strike=True)
    archers = CombatCreature("Keen-Eyed Archers", 2, 2, A, reach=True)
    disciple = CombatCreature("Golden-Tail Disciple", 2, 3, A, lifelink=True)
    nim = CombatCreature("Contagious Nim", 2, 2, A, infect=True)
    sphinx = CombatCreature("Goliath Sphinx", 8, 7, B, flying=True)
    state = GameState(
        players={
            A: PlayerState(
                life=19, poison=8, creatures=[billy, archers, disciple, nim]
            ),
            B: PlayerState(life=8, poison=8, creatures=[sphinx]),
        }
    )
    decide_optimal_blocks([billy, archers, disciple, nim], [sphinx], game_state=state)
    assert sphinx.blocking is nim
    sim = CombatSimulator([billy, archers, disciple, nim], [sphinx], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 6
    assert result.lifegain["A"] == 2
    assert nim in result.creatures_destroyed
    assert sphinx.minus1_counters == 2


def test_logged_scenario_21():
    """CR 702.19f: A blocking creature with trample assigns no damage to the attacking player."""
    A, B = "A", "B"
    sprite = CombatCreature("Moon Sprite", 1, 1, A, flying=True)
    sticker = CombatCreature("Nimble Birdsticker", 2, 3, A, reach=True)
    crew = CombatCreature("Wrecking Crew", 4, 5, B, reach=True, trample=True)
    state = GameState(
        players={
            A: PlayerState(life=3, creatures=[sprite, sticker]),
            B: PlayerState(life=4, creatures=[crew]),
        }
    )
    decide_optimal_blocks([sprite, sticker], [crew], game_state=state)
    assert crew.blocking is sticker
    sim = CombatSimulator([sprite, sticker], [crew], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert sticker in result.creatures_destroyed


def test_logged_scenario_22():
    """CR 702.78a: Persist returns the creature to the battlefield with a -1/-1 counter."""
    A, B = "A", "B"
    goblin = CombatCreature("Putrid Goblin", 2, 2, A, persist=True)
    mantis = CombatCreature("Highspire Mantis", 3, 3, A, flying=True, trample=True)
    scimitar = CombatCreature("Dancing Scimitar", 1, 5, A, flying=True)
    lammasu = CombatCreature("Venerable Lammasu", 5, 4, B, flying=True)
    sloth = CombatCreature("Relic Sloth", 4, 4, B, menace=True, vigilance=True)
    state = GameState(
        players={
            A: PlayerState(life=10, creatures=[goblin, mantis, scimitar]),
            B: PlayerState(life=13, creatures=[lammasu, sloth]),
        }
    )
    decide_optimal_blocks(
        [goblin, mantis, scimitar], [lammasu, sloth], game_state=state
    )
    assert lammasu.blocking is mantis
    assert sloth.blocking is goblin
    sim = CombatSimulator(
        [goblin, mantis, scimitar], [lammasu, sloth], game_state=state
    )
    result = sim.simulate()
    assert mantis in result.creatures_destroyed
    assert goblin not in result.creatures_destroyed
    assert goblin.minus1_counters == 1
    assert result.damage_to_players["B"] == 1


def test_logged_scenario_23():
    """CR 702.7b: Creatures with first strike deal combat damage before creatures without it."""
    A, B = "A", "B"
    observer = CombatCreature("Silent Observer", 1, 5, A, flying=True)
    butcher = CombatCreature("Smoldering Butcher", 4, 2, A, wither=True)
    knights = CombatCreature("Plover Knights", 3, 3, B, flying=True, first_strike=True)
    raptor = CombatCreature(
        "Anvilwrought Raptor", 2, 1, B, flying=True, first_strike=True
    )
    state = GameState(
        players={
            A: PlayerState(life=16, creatures=[observer, butcher]),
            B: PlayerState(life=16, creatures=[knights, raptor]),
        }
    )
    decide_optimal_blocks([observer, butcher], [knights, raptor], game_state=state)
    assert knights.blocking is observer
    assert raptor.blocking is butcher
    sim = CombatSimulator([observer, butcher], [knights, raptor], game_state=state)
    result = sim.simulate()
    assert butcher in result.creatures_destroyed
    assert observer.damage_marked == 3
    assert knights.damage_marked == 1


def test_logged_scenario_24():
    """CR 702.2b: Any nonzero damage from a creature with deathtouch is lethal."""
    A, B = "A", "B"
    devastator = CombatCreature("Eldrazi Devastator", 8, 9, A, trample=True)
    skygate = CombatCreature("Consulate Skygate", 0, 4, B, reach=True, defender=True)
    abomination = CombatCreature("Feral Abomination", 5, 5, B, deathtouch=True)
    patrol = CombatCreature("Skyhunter Patrol", 2, 3, B, flying=True, first_strike=True)
    state = GameState(
        players={
            A: PlayerState(life=18, creatures=[devastator]),
            B: PlayerState(life=5, creatures=[skygate, abomination, patrol]),
        }
    )
    decide_optimal_blocks(
        [devastator], [skygate, abomination, patrol], game_state=state
    )
    assert skygate.blocking is devastator
    assert abomination.blocking is devastator
    sim = CombatSimulator(
        [devastator], [skygate, abomination, patrol], game_state=state
    )
    result = sim.simulate()
    assert devastator in result.creatures_destroyed
    assert abomination in result.creatures_destroyed
    assert skygate.damage_marked == 3


def test_logged_scenario_25():
    """CR 702.19b & 702.2b: A trampler must assign lethal damage before assigning the rest to the defending player."""
    A, B = "A", "B"
    earth = CombatCreature("Earthshaking Si", 5, 5, A, trample=True)
    wall = CombatCreature("Wall of Wood", 0, 3, B, defender=True)
    crusader = CombatCreature("Cloud Crusader", 2, 3, B, flying=True, first_strike=True)
    recluse = CombatCreature("Deadly Recluse", 1, 2, B, reach=True, deathtouch=True)
    state = GameState(
        players={
            A: PlayerState(life=16, creatures=[earth]),
            B: PlayerState(life=17, creatures=[wall, crusader, recluse]),
        }
    )
    decide_optimal_blocks([earth], [wall, crusader, recluse], game_state=state)
    assert recluse.blocking is earth
    sim = CombatSimulator([earth], [wall, crusader, recluse], game_state=state)
    result = sim.simulate()
    assert earth in result.creatures_destroyed
    assert recluse in result.creatures_destroyed
    assert result.damage_to_players["B"] == 3


def test_logged_scenario_26():
    """CR 702.67a: Skulk prevents blocking by creatures with greater power."""
    A, B = "A", "B"
    eagle = CombatCreature("Sea Eagle", 1, 1, A, flying=True)
    homunculus = CombatCreature("Furtive Homunculus", 2, 1, A, skulk=True)
    barrier = CombatCreature("Hover Barrier", 0, 6, B, flying=True, defender=True)
    state = GameState(
        players={
            A: PlayerState(life=7, creatures=[eagle, homunculus]),
            B: PlayerState(life=19, creatures=[barrier]),
        }
    )
    decide_optimal_blocks([eagle, homunculus], [barrier], game_state=state)
    assert barrier.blocking is homunculus
    sim = CombatSimulator([eagle, homunculus], [barrier], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 1
    assert barrier.damage_marked == 2


def test_logged_scenario_27():
    """CR 702.13a: Intimidate limits blocking to artifact creatures or those sharing a color."""
    A, B = "A", "B"
    boar = CombatCreature("Bladetusk Boar", 3, 2, A, intimidate=True)
    mantis = CombatCreature("Highspire Mantis", 3, 3, A, flying=True, trample=True)
    rats = CombatCreature("Razortooth Rats", 2, 1, A, fear=True)
    dog = CombatCreature("Alpine Watchdog", 2, 2, A, vigilance=True)
    sanctuary = CombatCreature("Risen Sanctuary", 8, 8, B, vigilance=True)
    state = GameState(
        players={
            A: PlayerState(life=14, creatures=[boar, mantis, rats, dog]),
            B: PlayerState(life=11, creatures=[sanctuary]),
        }
    )
    decide_optimal_blocks([boar, mantis, rats, dog], [sanctuary], game_state=state)
    assert sanctuary.blocking is dog
    sim = CombatSimulator([boar, mantis, rats, dog], [sanctuary], game_state=state)
    result = sim.simulate()
    assert result.damage_to_players["B"] == 8
    assert dog in result.creatures_destroyed
    assert sanctuary.damage_marked == 2
