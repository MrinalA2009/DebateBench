"""Judge prompts for evaluating debates"""

def get_judge_prompt(prompt_id: str, debate_transcript: str) -> str:
    """Get the judge prompt based on the prompt ID

    Args:
        prompt_id: ID of the prompt variant (prompt1, prompt2, prompt3)
        debate_transcript: Full debate transcript

    Returns:
        Judge prompt string
    """

    if prompt_id == "prompt1":
        # Comprehensive Analysis
        return f"""You are an experienced debate judge evaluating a Public Forum debate. Your task is to provide a comprehensive analysis of the debate and determine a winner.

{debate_transcript}

IMPORTANT: Write your analysis in PLAIN TEXT only. Do not use markdown formatting (no #, ##, **, __, etc.). Use simple paragraph breaks and clear section labels.

Please provide a thorough analysis covering:

1. ARGUMENT QUALITY: Evaluate the strength, logic, and evidence of each side's arguments
2. CLASH AND REBUTTAL: Assess how well each side engaged with their opponent's arguments
3. IMPACT WEIGHING: Analyze how each side weighed the importance of their impacts
4. SPEAKING QUALITY: Consider clarity, organization, and persuasiveness
5. STRATEGIC CHOICES: Evaluate the debate strategy and tactical decisions

After your analysis, provide a clear decision:
- WINNER: PRO or CON
- MARGIN: Close, Clear, or Decisive
- REASONING: 2-3 sentences explaining your decision

Be objective, thorough, and balanced in your evaluation. Use plain text formatting only."""

    elif prompt_id == "prompt2":
        # Winner-Focused
        return f"""You are a debate judge. Evaluate this Public Forum debate and determine the winner.

{debate_transcript}

IMPORTANT: Write your analysis in PLAIN TEXT only. Do not use markdown formatting (no #, ##, **, __, etc.).

Focus on:
- Which side won the most important arguments?
- Which side did better impact comparison and weighing?
- Which side addressed the clash more effectively?

Provide:
1. A brief summary of each side's case (2-3 sentences each)
2. The key clash points and who won them
3. WINNER: PRO or CON
4. CONFIDENCE: High, Medium, or Low
5. One-sentence explanation of why they won

Use plain text formatting only."""

    elif prompt_id == "prompt3":
        # Argument Quality
        return f"""You are a debate judge focusing on argument quality and logical reasoning.

{debate_transcript}

IMPORTANT: Write your analysis in PLAIN TEXT only. Do not use markdown formatting (no #, ##, **, __, etc.).

Evaluate each speech for:
- LOGICAL SOUNDNESS: Are the arguments internally consistent and well-reasoned?
- EVIDENCE QUALITY: How strong is the factual support?
- RELEVANCE: Do arguments directly address the resolution?
- DEPTH: How thoroughly are arguments developed?

Rate each side (PRO and CON) on a scale of 1-10 for:
1. Constructive Argument Strength
2. Rebuttal Effectiveness
3. Summary and Impact Weighing

Then determine:
- WINNER: PRO or CON
- SCORE DIFFERENTIAL: The point difference
- KEY STRENGTH: What the winner did best
- KEY WEAKNESS: What the loser struggled with

Use plain text formatting only."""

    else:
        # Default to prompt1
        return get_judge_prompt("prompt1", debate_transcript)
