"""
reverse-prompt: Reverse-engineer prompts from example outputs using Claude/Mistral.

This module provides the ReversePromptEngine for reconstructing optimal prompts
based on example outputs, enabling unified voice across agents and quality gates.
"""

from .engine import ReversePromptEngine

__version__ = "0.1.0"
__author__ = "DomBot"
__all__ = ["ReversePromptEngine"]
