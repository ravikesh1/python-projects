"""JARVIS — an Iron Man-style AI assistant powered by the Claude API.

A text-first conversational assistant with a witty British-butler persona,
an optional voice mode, and a small set of built-in tools (date/time,
calculator, system info, and web search).
"""

from .assistant import Jarvis
from .cli import main

__all__ = ["Jarvis", "main"]
