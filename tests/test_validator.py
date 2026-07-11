"""Tests for response validation."""


from app.models import Role, RoleResult, ZipGroup, ZipResponse
from app.validator import validate_response


def make_zip_group(*role_names: str) -> ZipGroup:
    return ZipGroup(
        zip_code="10019",
        roles=[Role(name=n, gov_level="Federal", branch="Executive") for n in role_names],
        row_indices=list(range(2, 2 + len(role_names))),
    )


def make_result(
    role: str, name: str = "Joe Smith", website: str = "https://example.gov"
) -> RoleResult:
    return RoleResult(
        role=role,
        official_name=name,
        official_website=website,
        confidence=0.9,
        sources=["https://example.gov"],
    )


def make_response(*results: RoleResult) -> ZipResponse:
    return ZipResponse(zip_code="10019", results=list(results))


# --- valid responses ---


def test_valid_response_returns_no_errors() -> None:
    group = make_zip_group("Governor", "Mayor")
    response = make_response(make_result("Governor"), make_result("Mayor"))
    assert validate_response(response, group) == []


def test_single_role_valid() -> None:
    group = make_zip_group("President")
    response = make_response(make_result("President", "Donald Trump", "https://www.whitehouse.gov"))
    assert validate_response(response, group) == []


# --- missing roles ---


def test_missing_role_returns_error() -> None:
    group = make_zip_group("Governor", "Mayor")
    response = make_response(make_result("Governor"))  # Mayor missing
    errors = validate_response(response, group)
    assert len(errors) == 1
    assert "Mayor" in errors[0]


def test_all_roles_missing_returns_errors() -> None:
    group = make_zip_group("Governor", "Mayor")
    response = make_response()  # no results at all
    errors = validate_response(response, group)
    assert len(errors) == 1  # one error covering both missing roles
    assert "Governor" in errors[0] or "Mayor" in errors[0]


def test_extra_role_in_response_is_ignored() -> None:
    """Extra roles in the response beyond what was requested are not an error."""
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor"), make_result("Mayor"))
    assert validate_response(response, group) == []


# --- empty fields ---


def test_empty_official_name_returns_error() -> None:
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor", name=""))
    errors = validate_response(response, group)
    assert any("official_name" in e for e in errors)


def test_whitespace_only_name_returns_error() -> None:
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor", name="   "))
    errors = validate_response(response, group)
    assert any("official_name" in e for e in errors)


def test_empty_website_returns_error() -> None:
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor", website=""))
    errors = validate_response(response, group)
    assert any("official_website" in e for e in errors)


def test_whitespace_only_website_returns_error() -> None:
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor", website="  "))
    errors = validate_response(response, group)
    assert any("official_website" in e for e in errors)


# --- special values that are acceptable ---


def test_unknown_name_is_accepted() -> None:
    """'Unknown' is a valid response when the LLM cannot find the holder."""
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor", name="Unknown"))
    assert validate_response(response, group) == []


def test_na_name_is_accepted() -> None:
    """'N/A' is valid when the role does not apply to the ZIP."""
    group = make_zip_group("Borough President")
    response = make_response(make_result("Borough President", name="N/A"))
    assert validate_response(response, group) == []


def test_vacant_name_is_accepted() -> None:
    group = make_zip_group("Governor")
    response = make_response(make_result("Governor", name="Vacant"))
    assert validate_response(response, group) == []


# --- multiple errors ---


def test_multiple_errors_reported() -> None:
    group = make_zip_group("Governor", "Mayor")
    response = make_response(
        make_result("Governor", name="", website=""),
        # Mayor missing
    )
    errors = validate_response(response, group)
    assert len(errors) >= 2  # empty name, empty website, missing Mayor
