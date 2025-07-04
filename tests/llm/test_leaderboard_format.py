from llms.llm import LanguageModelName
from scripts.leaderboard import count_items
from scripts.leaderboard import format_accuracy_table
from scripts.leaderboard import format_pvalue_table
from scripts.leaderboard import standard_error
from scripts.leaderboard import two_proportion_p_value


def test_standard_error_zero_when_perfect():
    assert standard_error(1.0, 10) == 0.0
    assert standard_error(0.0, 10) == 0.0


def test_format_accuracy_table_sorted():
    res = {
        LanguageModelName.GPT_4O: [True, True],
        LanguageModelName.GPT_4_1: [True, False],
    }
    table = format_accuracy_table(res, 2)
    first_line = table.splitlines()[2]
    assert LanguageModelName.GPT_4O.value in first_line


def test_two_proportion_p_value_symmetric():
    r1 = [True, False, True]
    r2 = [False, True, False]
    p1 = two_proportion_p_value(r1, r2)
    p2 = two_proportion_p_value(r2, r1)
    assert abs(p1 - p2) < 1e-9


def test_format_pvalue_table_diagonal():
    res = {
        LanguageModelName.GPT_4O: [True, False],
        LanguageModelName.GPT_4_1: [False, True],
    }
    table = format_pvalue_table(res)
    lines = table.splitlines()
    cells = [c.strip() for c in lines[2].split("|") if c.strip()]
    assert cells[1] == "-"


def test_count_items_ignores_blank_lines(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("a\n\n\nb\n", encoding="utf8")
    assert count_items(str(path)) == 2
