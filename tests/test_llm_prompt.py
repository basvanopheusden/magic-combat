import asyncio
import pytest
from magic_combat import CombatCreature, GameState, PlayerState
from magic_combat.create_llm_prompt import create_llm_prompt, parse_block_assignments
from scripts.evaluate_random_combat_scenarios import call_openai_model

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
    async def create(self, model, messages, max_tokens=0, temperature=0):
        prompt = messages[0]["content"]
        return DummyResponse(f"response to {prompt}")


class DummyChat:
    def __init__(self):
        self.completions = DummyCompletions()

class DummyClient:
    def __init__(self):
        self.chat = DummyChat()
    async def aclose(self):
        pass


def test_create_prompt_contents():
    """CR 509.1a: The defending player chooses how creatures block."""
    atk = CombatCreature("Goblin", 2, 2, "A")
    blk = CombatCreature("Guard", 2, 3, "B")
    state = GameState(players={
        "A": PlayerState(life=20, creatures=[atk]),
        "B": PlayerState(life=20, creatures=[blk]),
    })
    prompt = create_llm_prompt(state, [atk], [blk])
    assert "The attackers are:" in prompt
    assert "Goblin" in prompt
    assert "The blockers are:" in prompt
    assert "Guard" in prompt


def test_parse_block_assignments():
    """CR 509.1a: The defending player chooses how creatures block."""
    text = "- Guard -> Goblin\n- Life total: 20"
    result = parse_block_assignments(text, ["Guard"], ["Goblin"])
    assert result == {"Guard": "Goblin"}


def test_call_openai_model(monkeypatch):
    """CR 509.1a: The defending player chooses how creatures block."""
    monkeypatch.setattr("openai.AsyncClient", lambda: DummyClient())
    res = asyncio.run(call_openai_model(["p1", "p2"]))
    assert res == "response to p1\n\nresponse to p2"
