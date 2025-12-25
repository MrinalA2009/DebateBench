"""DebateBench Protocol: Fixed debate format and rules"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


class SpeechType(Enum):
    """Fixed speech types in Public Forum debate format"""
    PRO_CONSTRUCTIVE = "pro_constructive"
    CON_CONSTRUCTIVE = "con_constructive"
    PRO_REBUTTAL = "pro_rebuttal"
    CON_REBUTTAL = "con_rebuttal"
    PRO_SUMMARY = "pro_summary"
    CON_SUMMARY = "con_summary"


# Word limits as specified in the plan
WORD_LIMITS = {
    SpeechType.PRO_CONSTRUCTIVE: 300,
    SpeechType.CON_CONSTRUCTIVE: 300,
    SpeechType.PRO_REBUTTAL: 250,
    SpeechType.CON_REBUTTAL: 250,
    SpeechType.PRO_SUMMARY: 200,
    SpeechType.CON_SUMMARY: 200,
}

# Fixed turn order
TURN_ORDER = [
    SpeechType.PRO_CONSTRUCTIVE,
    SpeechType.CON_CONSTRUCTIVE,
    SpeechType.PRO_REBUTTAL,
    SpeechType.CON_REBUTTAL,
    SpeechType.PRO_SUMMARY,
    SpeechType.CON_SUMMARY,
]


@dataclass
class Speech:
    """A single speech in a debate"""
    speech_type: SpeechType
    content: str
    word_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate word count against limit"""
        limit = WORD_LIMITS[self.speech_type]
        if self.word_count > limit:
            raise ValueError(
                f"Speech {self.speech_type.value} exceeds word limit: "
                f"{self.word_count} > {limit}"
            )


@dataclass
class Debate:
    """A complete debate following the fixed protocol"""
    resolution: str
    pro_model: str
    con_model: str
    speeches: List[Speech] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_speech(self, speech: Speech) -> None:
        """Add a speech, enforcing turn order"""
        expected_type = TURN_ORDER[len(self.speeches)]
        if speech.speech_type != expected_type:
            raise ValueError(
                f"Expected {expected_type.value}, got {speech.speech_type.value}"
            )
        self.speeches.append(speech)
    
    def is_complete(self) -> bool:
        """Check if debate has all required speeches"""
        return len(self.speeches) == len(TURN_ORDER)
    
    def get_transcript(self) -> str:
        """Get full debate transcript"""
        lines = [f"Resolution: {self.resolution}\n"]
        lines.append(f"Pro: {self.pro_model} | Con: {self.con_model}\n")
        lines.append("=" * 80 + "\n")
        
        for speech in self.speeches:
            lines.append(f"[{speech.speech_type.value.upper()}]")
            lines.append(f"Word count: {speech.word_count}/{WORD_LIMITS[speech.speech_type]}")
            lines.append(f"{speech.content}\n")
            lines.append("-" * 80 + "\n")
        
        return "\n".join(lines)


class DebateProtocol:
    """Fixed debate protocol enforcing Public Forum format"""
    
    def __init__(self):
        self.word_limits = WORD_LIMITS.copy()
        self.turn_order = TURN_ORDER.copy()
    
    def get_word_limit(self, speech_type: SpeechType) -> int:
        """Get word limit for a speech type"""
        return self.word_limits[speech_type]
    
    def get_next_speech_type(self, current_speech_count: int) -> Optional[SpeechType]:
        """Get the next speech type in the fixed order"""
        if current_speech_count >= len(self.turn_order):
            return None
        return self.turn_order[current_speech_count]
    
    def validate_speech(self, speech_type: SpeechType, content: str) -> tuple[bool, Optional[str]]:
        """Validate a speech against the protocol rules"""
        word_count = len(content.split())
        limit = self.get_word_limit(speech_type)
        
        if word_count > limit:
            return False, f"Exceeded word limit: {word_count} > {limit}"
        
        return True, None
    
    def count_words(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    def get_protocol_summary(self) -> str:
        """Get a summary of the protocol rules"""
        lines = ["DebateBench Protocol - Public Forum Format"]
        lines.append("=" * 50)
        lines.append("\nFixed Turn Order:")
        for i, speech_type in enumerate(self.turn_order, 1):
            limit = self.word_limits[speech_type]
            lines.append(f"  {i}. {speech_type.value}: {limit} words")
        return "\n".join(lines)

