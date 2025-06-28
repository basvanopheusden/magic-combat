import asyncio

from magic_combat import CombatCreature, GameState, PlayerState
from magic_combat.create_llm_prompt import create_llm_prompt, parse_block_assignments
from magic_combat.llm_cache import MockLLMCache
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
    prompt = create_llm_prompt(state, [atk], [blk])
    assert "The attackers are:" in prompt
    assert "Goblin" in prompt
    assert "The blockers are:" in prompt
    assert "Guard" in prompt


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


def test_call_openai_model(monkeypatch):
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: DummyClient())
    res = asyncio.run(call_openai_model(["p1", "p2"]))
    assert res == "response to p1\n\nresponse to p2"


def test_llm_cache_hit(monkeypatch):
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: DummyClient())
    cache = MockLLMCache()
    res1 = asyncio.run(
        call_openai_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    res2 = asyncio.run(
        call_openai_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    assert res1 == res2
    # Only one API call should have been made
    assert cache.entries[0]["response"] == res1
    assert len(cache.entries) == 1


def test_llm_cache_miss(monkeypatch):
    monkeypatch.setattr("openai.AsyncOpenAI", lambda: DummyClient())
    cache = MockLLMCache()
    res1 = asyncio.run(
        call_openai_model(["p1"], model="m", temperature=0.3, seed=1, cache=cache)
    )
    res2 = asyncio.run(
        call_openai_model(["p1"], model="m2", temperature=0.3, seed=1, cache=cache)
    )
    res3 = asyncio.run(
        call_openai_model(["p1"], model="m", temperature=0.4, seed=1, cache=cache)
    )
    res4 = asyncio.run(
        call_openai_model(["p1"], model="m", temperature=0.3, seed=2, cache=cache)
    )
    assert res1 != ""
    assert res2 != ""
    assert res3 != ""
    assert res4 != ""
    # Four distinct entries due to parameter differences
    assert len(cache.entries) == 4
