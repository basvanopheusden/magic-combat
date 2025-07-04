from llms.create_llm_prompt import parse_block_assignments


def test_dash_bullet_parsing():
    text = "- Guard -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {"Guard": "Goblin"}
    assert not invalid


def test_star_bullet_parsing():
    text = "* Guard -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {"Guard": "Goblin"}
    assert not invalid


def test_unicode_bullet_parsing():
    text = "\u2022 Guard -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {"Guard": "Goblin"}
    assert not invalid


def test_extra_spaces_handled():
    text = " -  Guard  ->  Goblin  "
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {"Guard": "Goblin"}
    assert not invalid


def test_case_insensitive_no_blocks():
    text = "No Blocks"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {}
    assert not invalid
