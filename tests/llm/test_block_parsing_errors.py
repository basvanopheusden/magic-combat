import pytest

from llms.create_llm_prompt import parse_block_assignments
from magic_combat.exceptions import UnparsableLLMOutputError


def test_no_assignment_lines_raises_error():
    text = "Some random text\nAnother line"
    with pytest.raises(UnparsableLLMOutputError):
        parse_block_assignments(text, ["Guard"], ["Goblin"])


def test_only_whitespace_raises_error():
    text = "   \n \n"
    with pytest.raises(UnparsableLLMOutputError):
        parse_block_assignments(text, ["Guard"], ["Goblin"])


def test_none_and_assignments_parsed():
    text = "None\n- Guard -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {"Guard": "Goblin"}
    assert not invalid


def test_extraneous_lines_ignored():
    text = "Analysis\n- Guard -> Goblin"
    pairs, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert pairs == {"Guard": "Goblin"}
    assert not invalid
