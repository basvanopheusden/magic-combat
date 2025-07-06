import asyncio

from llms.llm import LanguageModelName
from scripts.leaderboard import compute_elo_error_bars
from scripts.leaderboard import compute_elo_ratings
from scripts.leaderboard import count_items
from scripts.leaderboard import evaluate_models
from scripts.leaderboard import format_elo_table
from scripts.leaderboard import format_leaderboard_table
from scripts.leaderboard import format_pvalue_table
from scripts.leaderboard import standard_error
from scripts.leaderboard import two_proportion_p_value


def test_count_items(tmp_path):
    path = tmp_path / "d.jsonl"
    path.write_text("{}\n{}\n", encoding="utf8")
    assert count_items(str(path)) == 2


def test_standard_error():
    assert abs(standard_error(0.5, 100) - 0.05) < 1e-6


def test_two_proportion_p_value():
    r1 = [True] * 10
    r2 = [False] * 10
    p = two_proportion_p_value(r1, r2)
    assert p < 0.05


async def dummy_evaluate_dataset(
    path: str, *, model: LanguageModelName = LanguageModelName.GPT_4O, **kwargs
) -> list[bool]:
    return {
        LanguageModelName.GPT_4O: [True, False],
        LanguageModelName.GPT_4_1: [True, True],
    }[model]


def test_evaluate_models(monkeypatch):
    monkeypatch.setattr("scripts.leaderboard.evaluate_dataset", dummy_evaluate_dataset)
    res = asyncio.run(
        evaluate_models(
            "d.jsonl",
            [LanguageModelName.GPT_4O, LanguageModelName.GPT_4_1],
        )
    )
    assert res == {
        LanguageModelName.GPT_4O: [True, False],
        LanguageModelName.GPT_4_1: [True, True],
    }


def test_format_leaderboard_table():
    res = {
        LanguageModelName.GPT_4O: [True, False],
        LanguageModelName.GPT_4_1: [True, True],
    }
    ratings = compute_elo_ratings(res)
    err = compute_elo_error_bars(res, reps=5, seed=0)
    table = format_leaderboard_table(res, 2, ratings, err)
    assert "Model" in table and "Elo" in table


def test_format_pvalue_table():
    res = {
        LanguageModelName.GPT_4O: [True, False],
        LanguageModelName.GPT_4_1: [True, True],
    }
    table = format_pvalue_table(res)
    assert LanguageModelName.GPT_4O.value in table


def test_compute_elo_ratings():
    res = {
        LanguageModelName.GPT_4O: [True, True],
        LanguageModelName.GPT_4_1: [True, False],
        LanguageModelName.O3: [False, False],
    }
    ratings = compute_elo_ratings(res)
    assert (
        ratings[LanguageModelName.GPT_4O]
        > ratings[LanguageModelName.GPT_4_1]
        > ratings[LanguageModelName.O3]
    )


def test_compute_elo_error_bars():
    res = {
        LanguageModelName.GPT_4O: [True, False, True, False],
        LanguageModelName.GPT_4_1: [False, True, False, True],
    }
    err = compute_elo_error_bars(res, reps=5, seed=1)
    assert set(err.keys()) == set(res.keys())
    assert all(e >= 0 for e in err.values())


def test_format_elo_table():
    res = {
        LanguageModelName.GPT_4O: [True, True],
        LanguageModelName.GPT_4_1: [True, False],
        LanguageModelName.O3: [False, False],
    }
    ratings = compute_elo_ratings(res)
    err = compute_elo_error_bars(res, reps=5, seed=0)
    table = format_elo_table(ratings, err)
    assert "Elo" in table and LanguageModelName.GPT_4O.value in table
