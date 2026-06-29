"""
MyAgent - Structured Prompts
Loads agent prompts from markdown files following the ======== section format.
"""

from pathlib import Path
from functools import lru_cache

PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=10)
def load_prompt(agent_name: str) -> str:
    """
    Load a structured prompt from its markdown file.
    
    Args:
        agent_name: One of 'supervisor', 'energia', 'logistica', 'soporte'
    
    Returns:
        Full prompt text
    """
    prompt_file = PROMPTS_DIR / f"{agent_name}_prompt.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def get_supervisor_prompt() -> str:
    """Get the supervisor/router prompt."""
    return load_prompt("supervisor")


def get_energia_prompt() -> str:
    """Get the energy agent prompt."""
    return load_prompt("energia")


def get_logistica_prompt() -> str:
    """Get the logistics agent prompt."""
    return load_prompt("logistica")


def get_soporte_prompt() -> str:
    """Get the support agent prompt."""
    return load_prompt("soporte")
