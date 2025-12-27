"""Debate runner that orchestrates debates using the protocol"""

from typing import Optional, Literal
from .protocol import DebateProtocol, SpeechType, Debate, Speech, WORD_LIMITS
from .client import OpenRouterClient
from .prompts import get_debate_prompt, get_structured_debate_prompt, get_freeform_debate_prompt


class DebateRunner:
    """Runs debates following the DebateBench protocol"""
    
    def __init__(
        self,
        client: OpenRouterClient,
        temperature: float = 0.7,
        prompt_style: Literal["standard", "structured", "freeform"] = "standard"
    ):
        """Initialize debate runner
        
        Args:
            client: OpenRouterClient instance
            temperature: Temperature for model sampling (same for all speeches)
            prompt_style: Which prompt variant to use (for sensitivity studies)
        """
        self.client = client
        self.protocol = DebateProtocol()
        self.temperature = temperature
        self.prompt_style = prompt_style
    
    def _truncate_to_word_limit(self, text: str, word_limit: int) -> str:
        """Truncate text to word limit, trying to preserve sentence boundaries
        
        Args:
            text: Text to truncate
            word_limit: Maximum number of words
            
        Returns:
            Truncated text that ends at a sentence boundary if possible, or word boundary
        """
        words = text.split()
        if len(words) <= word_limit:
            return text
        
        # Try to find a sentence boundary near the word limit
        # Look for sentence endings (. ! ?) in the last 30% of allowed words
        search_start = max(0, word_limit - int(word_limit * 0.3))
        search_end = min(word_limit, len(words))
        
        # Look backwards from word_limit to find the last sentence ending
        best_cut_point = word_limit
        for i in range(search_end - 1, search_start - 1, -1):
            # Check if this word ends with sentence punctuation (after stripping whitespace)
            word = words[i].strip()
            if word and len(word) > 0 and word[-1] in '.!?':
                # Found a sentence boundary - use this as the cut point
                best_cut_point = i + 1
                break
        
        # Truncate at the best cut point (sentence boundary or word limit)
        truncated_words = words[:best_cut_point]
        return " ".join(truncated_words)
    
    def generate_speech(
        self,
        speech_type: SpeechType,
        debate: Debate,
        model: str,
        side: str
    ) -> Speech:
        """Generate a single speech
        
        Args:
            speech_type: Type of speech to generate
            debate: Current debate state
            model: Model identifier to use
            side: "PRO" or "CON"
            
        Returns:
            Speech object
        """
        # Get previous speeches as text
        previous_speeches = [s.content for s in debate.speeches]
        
        # Choose prompt style
        if self.prompt_style == "structured":
            prompt_text = get_structured_debate_prompt(
                speech_type, debate.resolution, previous_speeches, model, side
            )
        elif self.prompt_style == "freeform":
            prompt_text = get_freeform_debate_prompt(
                speech_type, debate.resolution, previous_speeches, model, side
            )
        else:
            prompt_text = get_debate_prompt(
                speech_type, debate.resolution, previous_speeches, model, side
            )
        
        # Calculate max tokens with a buffer to allow complete responses
        # We'll enforce word limits in post-processing, not at the API level
        # This prevents mid-sentence cuts from token limits
        word_limit = WORD_LIMITS[speech_type]
        # Allow more tokens (about 50% buffer) so model can finish sentences naturally
        # Average is ~1.3 tokens per word, so we give plenty of headroom
        max_tokens = int(word_limit * 2.0)  # 2x buffer allows natural sentence completion
        
        # Call model using LangChain format
        messages = [
            {"role": "system", "content": "You are a skilled debater participating in a structured debate."},
            {"role": "user", "content": prompt_text}
        ]
        
        print(f"\n{'='*80}")
        print(f"[SPEECH GENERATION] Starting {speech_type.value.upper()}")
        print(f"  Model: {model}")
        print(f"  Side: {side}")
        print(f"  Word limit: {word_limit}")
        print(f"  Max tokens: {max_tokens}")
        print(f"{'='*80}\n")
        
        try:
            response = self.client.call_model(
                model=model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            print(f"[RAW RESPONSE] Received response from {model}:")
            print(f"  Length: {len(response)} characters")
            print(f"  First 200 chars: {response[:200]}...")
            print(f"  Last 200 chars: ...{response[-200:]}")
            print()
        except Exception as e:
            print(f"[ERROR] Failed to call model {model}: {str(e)}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise
        
        # Use raw response from model - no cleaning or processing
        # Just strip leading/trailing whitespace
        response = response.strip()
        
        word_count = self.protocol.count_words(response)
        
        # Intelligently truncate if needed, trying to preserve sentence boundaries
        was_truncated = False
        if word_count > word_limit:
            print(f"[WARNING] Response exceeded word limit: {word_count} > {word_limit}, truncating intelligently...")
            response = self._truncate_to_word_limit(response, word_limit)
            word_count = self.protocol.count_words(response)
            was_truncated = True
        
        print(f"[CLEANED RESPONSE] After processing:")
        print(f"  Word count: {word_count}/{word_limit}")
        print(f"  Was truncated: {was_truncated}")
        print(f"  Full content ({len(response)} chars):")
        print(f"{'-'*80}")
        print(response)
        print(f"{'-'*80}\n")
        
        # Create and validate speech
        speech = Speech(
            speech_type=speech_type,
            content=response,
            word_count=word_count
        )
        
        print(f"[SPEECH CREATED] Successfully created speech object:")
        print(f"  Speech type: {speech.speech_type.value}")
        print(f"  Word count: {speech.word_count}")
        print(f"  Content length: {len(speech.content)} chars")
        print(f"{'='*80}\n")
        
        return speech
    
    def run_debate(
        self,
        resolution: str,
        pro_model: str,
        con_model: str,
        verbose: bool = True
    ) -> Debate:
        """Run a complete debate following the fixed protocol
        
        Args:
            resolution: Debate resolution (e.g., "Resolved: Social media does more harm than good")
            pro_model: Model identifier for PRO side
            con_model: Model identifier for CON side
            verbose: Whether to print progress
            
        Returns:
            Complete Debate object
        """
        debate = Debate(
            resolution=resolution,
            pro_model=pro_model,
            con_model=con_model
        )
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"Starting Debate: {resolution}")
            print(f"PRO: {pro_model} | CON: {con_model}")
            print(f"{'='*80}\n")
        
        # Generate each speech in fixed order
        for speech_type in self.protocol.turn_order:
            # Determine which model and side
            if "pro" in speech_type.value:
                model = pro_model
                side = "PRO"
            else:
                model = con_model
                side = "CON"
            
            if verbose:
                print(f"[{speech_type.value.upper()}] Generating... (limit: {WORD_LIMITS[speech_type]} words)")
            
            # Generate speech
            speech = self.generate_speech(speech_type, debate, model, side)
            debate.add_speech(speech)
            
            if verbose:
                print(f"  Generated {speech.word_count}/{WORD_LIMITS[speech_type]} words")
                print(f"  Preview: {speech.content[:100]}...\n")
        
        if verbose:
            print(f"{'='*80}")
            print("Debate Complete!")
            print(f"{'='*80}\n")
        
        return debate

