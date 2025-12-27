"""Debate prompts for each speech type"""

from .protocol import SpeechType, WORD_LIMITS


def get_debate_prompt(
    speech_type: SpeechType,
    resolution: str,
    previous_speeches: list[str],
    model_name: str,
    side: str  # "PRO" or "CON"
) -> str:
    """Generate prompt for a debate speech
    
    Args:
        speech_type: Type of speech to generate
        resolution: Debate resolution
        previous_speeches: List of previous speeches (in order)
        model_name: Name of the model making the speech
        side: Which side the model is arguing ("PRO" or "CON")
        
    Returns:
        Prompt string for the model
    """
    word_limit = WORD_LIMITS[speech_type]
    side_name = "Affirmative" if side == "PRO" else "Negative"
    
    # Base instructions
    base_instructions = f"""You are participating in a Public Forum debate. 

Resolution: {resolution}
Your side: {side_name} ({side})
Speech type: {speech_type.value}

WORD LIMIT: {word_limit} words target (aim for approximately {word_limit} words)
Please aim to write around {word_limit} words. While the system will handle minor overages, try to stay close to this limit for consistency.

Guidelines:
- Target approximately {word_limit} words in your response
- Write a complete, coherent speech within this general length
- Focus on making clear, well-structured arguments
- Make clear, well-structured arguments
- Use evidence and reasoning
- Respond to previous arguments when applicable
- Write in plain text only (no markdown, LaTeX, or special formatting)
- Use proper spacing between words and sentences
"""

    # Speech-specific instructions
    if "constructive" in speech_type.value:
        instructions = f"""{base_instructions}
This is your constructive speech. Present your core arguments in favor of your side.
- Clearly state your main claims
- Provide reasoning and evidence
- Establish a framework for evaluating the debate
"""
    elif "rebuttal" in speech_type.value:
        instructions = f"""{base_instructions}
This is your rebuttal speech. Respond to your opponent's arguments.
- Address their main points directly
- Refute their claims with counter-evidence and reasoning
- Rebuild your own arguments that were attacked
"""
    elif "summary" in speech_type.value:
        instructions = f"""{base_instructions}
This is your summary speech. Synthesize the debate and make your final case.
- Summarize the key points of clash
- Weigh impacts and explain why your side wins
- Make final persuasive appeals
"""
    
    # Add previous speeches context
    if previous_speeches:
        instructions += "\nPrevious speeches in the debate:\n"
        for i, speech in enumerate(previous_speeches, 1):
            instructions += f"\n--- Speech {i} ---\n{speech}\n"
    
    instructions += f"\nNow write your {speech_type.value} speech ({side} side). Remember: MAXIMUM {word_limit} words - if you exceed this limit, your speech will be cut off. Count your words and stop before reaching {word_limit} words."
    
    return instructions


def get_structured_debate_prompt(
    speech_type: SpeechType,
    resolution: str,
    previous_speeches: list[str],
    model_name: str,
    side: str,
    emphasize_clash: bool = True
) -> str:
    """Generate a structured debate prompt with explicit clash instructions
    
    This is an alternative prompt variant for sensitivity studies.
    """
    base_prompt = get_debate_prompt(speech_type, resolution, previous_speeches, model_name, side)
    
    if emphasize_clash and "rebuttal" in speech_type.value:
        clash_instruction = "\n\nIMPORTANT: You must directly clash with your opponent's arguments. For each major point they made, either:\n- Show why their evidence is flawed\n- Show why their reasoning is incorrect\n- Show why their impacts are outweighed by yours\n"
        base_prompt = base_prompt.replace(
            "Now write your",
            clash_instruction + "Now write your"
        )
    
    return base_prompt


def get_freeform_debate_prompt(
    speech_type: SpeechType,
    resolution: str,
    previous_speeches: list[str],
    model_name: str,
    side: str
) -> str:
    """Generate a freeform debate prompt (minimal structure)
    
    This is an alternative prompt variant for sensitivity studies.
    """
    word_limit = WORD_LIMITS[speech_type]
    side_name = "Affirmative" if side == "PRO" else "Negative"
    
    prompt = f"""You are arguing the {side_name} side of this resolution: {resolution}

WORD LIMIT: {word_limit} words target (aim for approximately {word_limit} words)
Please aim to write around {word_limit} words. While the system will handle minor overages, try to stay close to this limit for consistency.

Write a {speech_type.value} speech explaining why your side is correct.
- Target approximately {word_limit} words
- Write a complete, coherent response

Write in plain text only (no markdown, LaTeX, or special formatting). Use proper spacing between words.
"""
    
    if previous_speeches:
        prompt += "\nYour opponent has made these points:\n"
        for speech in previous_speeches:
            prompt += f"{speech}\n\n"
        prompt += "Respond as you see fit.\n"
    
    return prompt

