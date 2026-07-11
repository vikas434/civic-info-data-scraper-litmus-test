"""Semantic validation of LLM responses against expected ZIP group roles."""

from __future__ import annotations

from app.models import ZipGroup, ZipResponse


def validate_response(response: ZipResponse, zip_group: ZipGroup) -> list[str]:
    """Validate that a ZipResponse is complete and contains non-empty data.

    Checks performed:
    - All roles from the ZipGroup appear in the response.
    - No result has an empty official_name or official_website.

    Note: Values like "Unknown", "N/A", and "Vacant" are accepted — they represent
    legitimate LLM answers when the holder cannot be found or the role does not apply.

    Args:
        response: The structured LLM response to validate.
        zip_group: The ZIP group whose roles were requested.

    Returns:
        A list of error message strings. Empty list means the response is valid.
    """
    errors: list[str] = []

    expected_roles = {role.name for role in zip_group.roles}
    returned_roles = {result.role for result in response.results}

    missing = expected_roles - returned_roles
    if missing:
        errors.append(f"Missing roles in response: {sorted(missing)}")

    for result in response.results:
        if not result.official_name.strip():
            errors.append(f"Empty official_name for role '{result.role}'")
        if not result.official_website.strip():
            errors.append(f"Empty official_website for role '{result.role}'")

    return errors
