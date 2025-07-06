from llms.create_llm_prompt import create_llm_prompt
from llms.create_llm_prompt import parse_block_assignments
from magic_combat import Color
from magic_combat import CombatCreature
from magic_combat import GameState
from magic_combat import PlayerState


class DummyMessage:
    def __init__(self, content):
        self.content = content


class DummyChoice:
    def __init__(self, content):
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]


class DummyCompletions:
    def __init__(self):
        self.calls = 0

    async def create(self, model, messages, max_tokens=0, temperature=0):
        self.calls += 1
        prompt = messages[0]["content"]
        return DummyResponse(f"response to {prompt}")


class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()


class DummyClient:
    def __init__(self):
        self.chat = DummyChat()

    async def close(self):
        pass


def test_create_prompt_contents():
    atk = CombatCreature("Goblin", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 3, "B")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    prompt = create_llm_prompt(state)
    assert "The attackers are:" in prompt
    assert "Goblin" in prompt
    assert "The blockers are:" in prompt
    assert "Guard" in prompt


def test_prompt_includes_mana_cost():
    atk = CombatCreature("Zombie", 3, 3, "A", mana_cost="{2}{B}")
    blk = CombatCreature("Cleric", 1, 4, "B", mana_cost="{1}{W}")
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    prompt = create_llm_prompt(state)
    assert "{2}{B}" in prompt
    assert "{1}{W}" in prompt


def test_prompt_includes_colors_when_relevant():
    """CR 702.13b: Intimidate checks color of potential blockers."""
    atk = CombatCreature("Rogue", 2, 2, "A", intimidate=True, colors={Color.GREEN})
    blk = CombatCreature("Guard", 2, 2, "B", colors={Color.BLUE})
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[atk]),
            "B": PlayerState(life=20, creatures=[blk]),
        }
    )
    prompt = create_llm_prompt(state)
    assert "[Green]" in prompt
    assert "[Blue]" in prompt


def test_parse_block_assignments():
    text = "- Guard -> Goblin\n- Life total: 20"
    result, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert not invalid
    assert result == {"Guard": "Goblin"}


def test_parse_block_assignments_none():
    text = "None"
    result, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert result == {}
    assert not invalid


def test_parse_block_assignments_invalid_name():
    text = "- Foo -> Goblin"
    result, invalid = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert invalid
    assert result == {}


def test_prompt_includes_example_lines():
    state = GameState(
        players={
            "A": PlayerState(life=20, creatures=[]),
            "B": PlayerState(life=20, creatures=[]),
        }
    )
    prompt = create_llm_prompt(state)
    assert "flanking 2" in prompt
    assert "+1/+1 counters" in prompt
