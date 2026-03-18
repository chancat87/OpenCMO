"""ENV-driven configuration system."""

import os

_MODEL_DEFAULT = "gpt-4o"


def get_model(agent_name: str) -> str:
    """Return the model for a given agent.

    Resolution order:
        OPENCMO_MODEL_{AGENT} > OPENCMO_MODEL_DEFAULT > 'gpt-4o'
    """
    specific = os.environ.get(f"OPENCMO_MODEL_{agent_name.upper()}")
    if specific:
        return specific
    return os.environ.get("OPENCMO_MODEL_DEFAULT", _MODEL_DEFAULT)
