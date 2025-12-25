"""Example usage of DebateBench"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from debatebench import DebateRunner, OpenRouterClient, DebateProtocol

# Initialize - API key is loaded from .env file automatically
client = OpenRouterClient()
runner = DebateRunner(client, temperature=0.7)

# Example debate
resolution = "Resolved: Social media does more harm than good"

# Run debate
debate = runner.run_debate(
    resolution=resolution,
    pro_model="openai/gpt-4",
    con_model="anthropic/claude-3-opus",
    verbose=True
)

# Get transcript
print(debate.get_transcript())

# Save to file
with open("debate_transcript.txt", "w") as f:
    f.write(debate.get_transcript())

print("\nDebate saved to debate_transcript.txt")

