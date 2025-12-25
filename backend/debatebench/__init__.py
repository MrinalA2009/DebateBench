"""DebateBench: A Controlled Debate Benchmark"""

from .protocol import DebateProtocol, SpeechType, Speech, Debate
from .client import OpenRouterClient
from .runner import DebateRunner

__version__ = "0.1.0"
__all__ = ["DebateProtocol", "SpeechType", "Speech", "Debate", "OpenRouterClient", "DebateRunner"]

