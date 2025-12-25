# Prompt Types Explanation

DebateBench supports three different prompt styles for sensitivity studies. These allow you to test how prompt variations affect debate outcomes.

## Standard (Default)

**What it is:** A structured, detailed prompt that follows Public Forum debate conventions.

**Features:**
- Clear instructions about speech type (constructive, rebuttal, summary)
- Specific guidance for each speech type
- Word limit enforcement
- Context from previous speeches
- Framework for evaluation

**When to use:** For normal debates where you want consistent, high-quality arguments following debate norms.

**Example structure:**
```
You are participating in a Public Forum debate.
Resolution: [resolution]
Your side: Affirmative (PRO)
Speech type: pro_constructive
Word limit: 300 words (STRICT)

Rules:
- Stay within the word limit
- Make clear, well-structured arguments
- Use evidence and reasoning
- Respond to previous arguments when applicable

This is your constructive speech. Present your core arguments...
```

## Structured

**What it is:** Similar to Standard, but with **explicit clash instructions** for rebuttal speeches.

**Features:**
- All features of Standard prompt
- **Additional emphasis on direct clash** in rebuttals
- Explicit instructions to address opponent's points systematically
- More directive about how to structure refutations

**When to use:** When you want to test if explicit clash instructions change debate quality or outcomes.

**Key difference:** Rebuttal speeches get extra instructions like:
```
IMPORTANT: You must directly clash with your opponent's arguments. 
For each major point they made, either:
- Show why their evidence is flawed
- Show why their reasoning is incorrect
- Show why their impacts are outweighed by yours
```

## Freeform

**What it is:** A minimal prompt with little structure or guidance.

**Features:**
- Very brief instructions
- No specific debate format guidance
- No explicit clash requirements
- Just basic task description

**When to use:** For sensitivity studies to see how much prompt structure matters. This tests if models can debate effectively with minimal guidance.

**Example structure:**
```
You are arguing the Affirmative side of this resolution: [resolution]

Write a pro_constructive speech (max 300 words) explaining why your side is correct.

Your opponent has made these points:
[previous speeches]

Respond as you see fit.
```

## Why This Matters

According to the DebateBench research plan, **prompt sensitivity is a major confounder** in debate benchmarks. The same models might perform differently depending on which prompt style is used. By testing all three, you can:

1. **Measure prompt impact:** See how much prompt choice affects win rates
2. **Test robustness:** Determine if rankings are stable across prompt variations
3. **Identify confounders:** Understand if prompt effects rival model choice effects

This is Contribution C4 from the research plan: "Prompt Sensitivity as a Benchmark Confounder"

