from scripts.investigate_scenario import investigate_scenario


def test_investigate_scenario_output(capsys):
    investigate_scenario("tests/data/example_test_cards.json", seed=123)
    out = capsys.readouterr().out
    assert "Simple AI blocks:" in out
    assert "Optimal AI blocks:" in out
