from magic_combat import calculate_mana_value


def test_invalid_nested_braces():
    """CR 202.3a: Only properly formed mana symbols contribute to mana value."""
    result = calculate_mana_value("{{2}}{3}{{{4}}}", 0)
    assert result == 3


def test_simple_numeric():
    """CR 202.3: Each numeric symbol adds that amount of mana."""
    result = calculate_mana_value("{1}{2}{3}", 0)
    assert result == 6


def test_zero_mana():
    """CR 202.3: {0} contributes zero mana."""
    result = calculate_mana_value("{0}", 0)
    assert result == 0


def test_invalid_lowercase():
    """CR 202.1a: Mana symbols are case-sensitive."""
    result = calculate_mana_value("{w}{u}{b}{r}{g}{c}", 0)
    assert result == 0


def test_text_outside_braces():
    """CR 202.3: Only symbols inside braces count toward mana value."""
    result = calculate_mana_value("Pay {2}{W} to cast this spell", 0)
    assert result == 3


def test_single_color_letters():
    """CR 202.2: Single color symbols each contribute one mana."""
    result = calculate_mana_value("{W}{U}{B}{R}{G}", 0)
    assert result == 5


def test_x_mana_negative():
    """CR 202.3b: X uses the chosen value when calculating mana value."""
    result = calculate_mana_value("{X}{X}{3}", -2)
    assert result == -1


def test_invalid_symbols():
    """CR 202.1a: Unrecognized symbols contribute no mana."""
    result = calculate_mana_value("{Z}{Q}{W/W}{P/W}{/}{}{2/3}", 0)
    assert result == 0


def test_x_mana_zero():
    """CR 202.3b: X can be zero when chosen as such."""
    result = calculate_mana_value("{X}{1}{X}", 0)
    assert result == 1


def test_mixed_symbols():
    """CR 202.3: Mana value sums numeric, color, hybrid, and X symbols."""
    result = calculate_mana_value("{2}{W}{U/B}{G/P}{X}{C}", 3)
    assert result == 9


def test_complex_real_example():
    """CR 202.3b: Multiple X symbols use the chosen value."""
    result = calculate_mana_value("{X}{X}{W}{W}{U}{B}{R}{G}", 4)
    assert result == 14


def test_unmatched_braces():
    """CR 202.3a: Unmatched braces do not form valid mana symbols."""
    result = calculate_mana_value("{2}{3{4}5}", 0)
    assert result == 2


def test_case_sensitive_x():
    """CR 202.3b: Uppercase X is treated as the chosen value; lowercase is invalid."""
    result = calculate_mana_value("{X}{x}{2}", 10)
    assert result == 12


def test_x_mana_positive():
    """CR 202.3b: Positive values of X increase mana value accordingly."""
    result = calculate_mana_value("{X}{X}{2}", 5)
    assert result == 12


def test_large_numeric_values():
    """CR 202.3: Numeric symbols can represent large mana amounts."""
    result = calculate_mana_value("{100}{999}{0}", 0)
    assert result == 1099


def test_colorless_mana():
    """CR 202.2a: The colorless symbol {C} adds one mana."""
    result = calculate_mana_value("{C}{C}{C}", 0)
    assert result == 3


def test_empty_string():
    """CR 202.3a: With no symbols the mana value is zero."""
    result = calculate_mana_value("", 0)
    assert result == 0


def test_whitespace_in_symbols():
    """CR 202.1a: Symbols containing whitespace are invalid."""
    result = calculate_mana_value("{2 }{W }{ U}{B/ R}", 0)
    assert result == 0


def test_hybrid_mana():
    """CR 202.2d: Hybrid mana symbols contribute one mana."""
    result = calculate_mana_value("{W/U}{B/R}{G/W}{U/B}{R/G}", 0)
    assert result == 5


def test_phyrexian_mana():
    """CR 202.2e: Phyrexian mana symbols contribute one mana."""
    result = calculate_mana_value("{W/P}{U/P}{B/P}{R/P}{G/P}", 0)
    assert result == 5
