"""Prompts package containing system prompts, few-shot examples, and templates."""
from prompts.fact_check_prompts import (
    FACT_CHECKER_SYSTEM_PROMPT,
    FEW_SHOT_FACT_CHECK_EXAMPLES,
    REACT_AGENT_PROMPT
)
from prompts.digest_prompts import (
    DIGEST_EDITOR_SYSTEM_PROMPT,
    DIGEST_SYNTHESIS_TEMPLATE
)

__all__ = [
    "FACT_CHECKER_SYSTEM_PROMPT",
    "FEW_SHOT_FACT_CHECK_EXAMPLES",
    "REACT_AGENT_PROMPT",
    "DIGEST_EDITOR_SYSTEM_PROMPT",
    "DIGEST_SYNTHESIS_TEMPLATE",
]
