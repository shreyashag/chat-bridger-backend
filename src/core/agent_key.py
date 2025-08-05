from enum import Enum


class AgentKey(str, Enum):
    """Enum for agent keys."""

    CHAT_TITLE_RENAMER = "chat_title_renamer"
    HISTORY_TUTOR = "history_tutor"
    MATH_TUTOR = "math_tutor"
    TRIAGE_AGENT = "triage_agent"
