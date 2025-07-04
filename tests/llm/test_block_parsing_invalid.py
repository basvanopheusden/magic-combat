from llms.create_llm_prompt import parse_block_assignments


def test_duplicate_blocker_marked_invalid():
    text = "- Guard -> Goblin\n- Guard -> Elf"
    pairs, invalid = parse_block_assignments(
        text, ["Guard", "Squire"], ["Goblin", "Elf"]
    )
    assert pairs == {"Guard": "Goblin"}
    assert invalid


def test_unknown_blocker_marked_invalid():
    text = "- Foo -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {}
    assert invalid


def test_unknown_attacker_marked_invalid():
    text = "- Guard -> Foo"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {}
    assert invalid


def test_case_mismatch_marked_invalid():
    text = "- guard -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {}
    assert invalid
