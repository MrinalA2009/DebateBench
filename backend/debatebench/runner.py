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
        
        # Estimate max tokens (rough: 1 token ≈ 0.75 words, add buffer)
        word_limit = WORD_LIMITS[speech_type]
        max_tokens = int(word_limit / 0.75) + 50
        
        # Call model using LangChain format
        messages = [
            {"role": "system", "content": "You are a skilled debater participating in a structured debate."},
            {"role": "user", "content": prompt_text}
        ]
        
        response = self.client.call_model(
            model=model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens
        )
        
        # Clean and validate response
        response = response.strip()
        
        # Remove any LaTeX/markdown formatting that might cause issues
        import re
        # Remove LaTeX commands (e.g., \textbf{}, \textit{}, etc.)
        response = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', response)
        # Remove markdown formatting
        response = re.sub(r'\*\*([^*]+)\*\*', r'\1', response)  # Bold
        response = re.sub(r'\*([^*]+)\*', r'\1', response)  # Italic
        response = re.sub(r'#+\s*', '', response)  # Headers
        # Ensure proper spacing (fix cases where words run together)
        # Fix: number + lowercase word (e.g., "20million" -> "20 million")
        response = re.sub(r'([0-9]+)([a-z]+)', r'\1 \2', response)
        # Fix: lowercase word + number (e.g., "million20" -> "million 20")
        response = re.sub(r'([a-z]+)([0-9]+)', r'\1 \2', response)
        # Fix: word + uppercase word (camelCase, e.g., "socialmedia" -> "social media")
        response = re.sub(r'([a-z]+)([A-Z][a-z]+)', r'\1 \2', response)
        # Fix: common compound words that might have lost spaces
        # This is a heuristic - insert space before common words when they appear merged
        common_words = ['in', 'on', 'for', 'to', 'the', 'and', 'or', 'is', 'are', 'was', 'were', 'by', 'of', 'with']
        for word in common_words:
            # Fix: "wordin" or "wordIn" -> "word in"
            pattern = r'([a-z]+)' + word + r'([^a-z\s])'
            response = re.sub(pattern, r'\1 ' + word + r'\2', response, flags=re.IGNORECASE)
            # Fix: "inword" or "inWord" -> "in word"  
            pattern = r'([^a-z\s])' + word + r'([a-z]+)'
            response = re.sub(pattern, r'\1' + word + r' \2', response, flags=re.IGNORECASE)
        # Normalize whitespace
        response = ' '.join(response.split())
        
        word_count = self.protocol.count_words(response)
        
        # Truncate if needed (shouldn't happen, but safety)
        if word_count > word_limit:
            words = response.split()[:word_limit]
            response = " ".join(words)
            word_count = word_limit
        
        # Create and validate speech
        speech = Speech(
            speech_type=speech_type,
            content=response,
            word_count=word_count
        )
        
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

