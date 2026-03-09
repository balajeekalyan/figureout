"""Role definitions for FigureOut."""

from dataclasses import dataclass


@dataclass
class RoleDefinition:
    """Definition of a role for FigureOut.

    Attributes:
        prompt: System prompt for the LLM when this role is active.
        schema: JSON schema string describing the expected output format.
        guideline: Short description used by the classifier to route queries to this role.
    """

    prompt: str
    schema: str
    guideline: str


def build_classification_prompt(roles: dict[str, RoleDefinition]) -> str:
    """Build a classification prompt from a role registry.

    Args:
        roles: Mapping of role name → RoleDefinition containing the guideline.

    Returns:
        A system prompt string suitable for the classifier LLM call.
    """
    classifiable = {name: rd for name, rd in roles.items() if name != "off_topic"}
    role_list = ", ".join(f'"{name}"' for name in classifiable)
    guidelines = "\n".join(f"- {name}: {rd.guideline}" for name, rd in classifiable.items())
    return (
        "You are a classifier. Given a user query, determine which roles should handle it. "
        'Reply with ONLY a JSON object with a key "roles" containing a list of matching role '
        "strings ranked by relevance. "
        f"Choose from these values: {role_list}.\n\n"
        f"Guidelines:\n{guidelines}"
    )
