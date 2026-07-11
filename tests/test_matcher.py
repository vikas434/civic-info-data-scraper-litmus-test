"""Tests for fuzzy name and URL matching."""

from app.matcher import names_match, normalize_name, normalize_url, urls_match

# --- normalize_name ---


def test_normalize_name_lowercases() -> None:
    assert normalize_name("Kathy Hochul") == "kathy hochul"


def test_normalize_name_strips_whitespace() -> None:
    assert normalize_name("  Kathy Hochul  ") == "kathy hochul"


def test_normalize_name_removes_hon_title() -> None:
    assert normalize_name("Hon. Kathy Hochul") == "kathy hochul"


def test_normalize_name_removes_rep_title() -> None:
    assert normalize_name("Rep. Jerrold Nadler") == "jerrold nadler"


def test_normalize_name_collapses_extra_spaces() -> None:
    assert normalize_name("Kathy   Hochul") == "kathy hochul"


# --- normalize_url ---


def test_normalize_url_strips_https() -> None:
    assert normalize_url("https://www.ny.gov") == "ny.gov"


def test_normalize_url_strips_http() -> None:
    assert normalize_url("http://www.ny.gov") == "ny.gov"


def test_normalize_url_strips_www() -> None:
    assert normalize_url("https://www.ny.gov") == "ny.gov"


def test_normalize_url_strips_trailing_slash() -> None:
    assert normalize_url("https://ny.gov/governor/") == "ny.gov/governor"


def test_normalize_url_lowercases() -> None:
    assert normalize_url("https://NY.GOV") == "ny.gov"


# --- names_match ---


def test_names_match_exact() -> None:
    assert names_match("Kathy Hochul", "Kathy Hochul") is True


def test_names_match_case_insensitive() -> None:
    assert names_match("kathy hochul", "Kathy Hochul") is True


def test_names_match_with_title() -> None:
    assert names_match("Kathy Hochul", "Gov. Kathy Hochul") is True


def test_names_match_middle_name_omitted() -> None:
    assert names_match("Zohran Kwame Mamdani", "Zohran Mamdani") is True


def test_names_match_completely_different() -> None:
    assert names_match("Kathy Hochul", "Eric Adams") is False


def test_names_match_partial_overlap_not_enough() -> None:
    # "Eric" appears in neither — different people
    assert names_match("Eric Adams", "Eric Holder") is False


# --- urls_match ---


def test_urls_match_identical() -> None:
    assert urls_match("https://www.ny.gov/governor", "https://www.ny.gov/governor") is True


def test_urls_match_http_vs_https() -> None:
    assert urls_match("http://ny.gov/governor", "https://ny.gov/governor") is True


def test_urls_match_trailing_slash() -> None:
    assert urls_match("https://ny.gov/governor/", "https://ny.gov/governor") is True


def test_urls_match_www_vs_no_www() -> None:
    assert urls_match("https://www.ny.gov/governor", "https://ny.gov/governor") is True


def test_urls_no_match_different_path() -> None:
    assert urls_match("https://ny.gov/governor", "https://ny.gov/mayor") is False


def test_urls_no_match_different_domain() -> None:
    assert urls_match("https://ny.gov", "https://nyc.gov") is False
