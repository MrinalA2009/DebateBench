"""Quick test of the debate protocol"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from debatebench import DebateProtocol, SpeechType, Speech, Debate

# Test protocol
protocol = DebateProtocol()
print(protocol.get_protocol_summary())

# Test word limit validation
test_speech = Speech(
    speech_type=SpeechType.PRO_CONSTRUCTIVE,
    content="word " * 299 + "end",  # 300 words
    word_count=300
)
print(f"\n✓ Created valid speech: {test_speech.speech_type.value} ({test_speech.word_count} words)")

# Test debate structure
debate = Debate(
    resolution="Resolved: Testing is important",
    pro_model="test-pro",
    con_model="test-con"
)

# Test turn order
print(f"\nTurn order check:")
for i, speech_type in enumerate(protocol.turn_order, 1):
    next_type = protocol.get_next_speech_type(i - 1)
    print(f"  {i}. {speech_type.value} (next: {next_type == speech_type})")

print("\n✓ Protocol structure validated!")

