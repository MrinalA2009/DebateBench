# Revised Paper Plan

## Paper Thesis (One Sentence — Lock This)

We study the reliability of AI-generated debate benchmarks by introducing a controlled Public Forum–style debate environment and a stability-tested AI judging protocol, showing when leaderboard rankings are meaningful—and when they are not.

This is the conceptual spine. Everything else supports it.

## Explicit Contributions (Final)

### C1 — DebateBench: A Controlled Debate Benchmark

**Research Question:**
How can AI debates be generated in a controlled, comparable, and reproducible way?

**Contribution:**
- A standardized Public Forum–style debate protocol:
  - Binary resolution
  - Fixed turn order
  - Strict word limits
- A curated topic set (300–500 resolutions)
- Open-source prompts, format constraints, and logging

**Why it matters:**
Most AI debate evaluations are uncontrolled demos; DebateBench enables fair cross-model comparison.

### C2 — JudgeBench: A Stability-Tested AI Judge

**Research Question:**
How can we design an AI judge whose decisions are internally consistent and robust to prompt variation?

**Contribution:**
- A rubric-based judging protocol aligned to PF norms
- Structured JSON-only outputs
- Empirical judge selection based on:
  - Repeatability (same debate, multiple judgments)
  - Prompt robustness (paraphrased judge prompts)
  - Side fairness (role swapping)

**Key insight:**
Judge stability is treated as a measurable property, not assumed.

### C3 — Leaderboard Reliability Analysis

**Research Question:**
When does an AI debate leaderboard become stable enough to trust?

**Contribution:**
- ELO-based leaderboard construction
- Convergence analysis vs. number of matches
- Bootstrap confidence intervals over rankings
- Sensitivity to topic subsampling and judge perturbations

**Key result (intended):**
Leaderboards can appear stable while remaining statistically unreliable.

### C4 — Prompt Sensitivity as a Benchmark Confounder

**Research Question:**
How much do debate prompts influence outcomes compared to model choice?

**Contribution:**
- Controlled prompt variants (structured vs freeform, clash-explicit vs implicit)
- Measurement of win-rate and ranking shifts
- Evidence that prompt choice can rival model choice in impact

**Framing:**
Prompt sensitivity is treated as a threat to benchmark validity, not a side study.

## Positioning vs Prior Work (Critical)

- Prior AI debate work focuses on performance.
- Prior LLM evaluation often assumes evaluator correctness.
- This paper focuses on evaluation reliability, similar in spirit to recent multi-agent benchmark work, but applied to real argumentation rather than toy games.

**You do not claim:**
- human-level judging
- alignment
- best debate model

## Benchmark Design

### 1. Scope (Conservative, Reviewer-Safe)

- Debate format: Public Forum–style (chosen for binary structure + clash)
- Topics: 300–500
- Models: 6–10
- Judge: one frozen model + prompt (selected empirically)
- Evaluation: AI-only (explicit limitation)

### 2. Dataset

#### 2.1 Topic Set

- Format: "Resolved: …"
- Binary stance
- 5–7 topical categories
- Balanced sampling
- No claim of exhaustiveness

#### 2.2 Debate Protocol

**Fixed Structure**
- Pro Constructive (300)
- Con Constructive (300)
- Pro Rebuttal (250)
- Con Rebuttal (250)
- Pro Summary (200)
- Con Summary (200)

**Controls**
- Identical prompts
- Identical temperature range
- Strict word limits
- Structured logging

## JudgeBench (Core Technical Section)

### 3. Judging Rubric

Each side scored 1–5 on:
- Argument quality
- Evidence & grounding
- Clash & refutation
- Impact weighing

Plus:
- Winner
- Confidence (0–1)
- ≤100-word reason

### 4. Judge Output Schema

```json
{
  "winner": "PRO | CON",
  "scores": {
    "argument_quality": {...},
    "evidence": {...},
    "clash": {...},
    "weighing": {...}
  },
  "confidence": 0.0,
  "short_reason": ""
}
```

### 5. Judge Selection Protocol (Critical)

**Candidates**
- 2–3 judge models
- 6–10 prompt variants

**Evaluation Metrics**
- Repeatability (same debate, multiple runs)
- Prompt robustness (paraphrase tests)
- Side fairness (role swap)

**Selection Rule**
Choose the configuration minimizing variance and bias. Freeze for all experiments.

## Leaderboard Construction

### 6. Match Protocol

- Two models debate same topic
- Run twice (side swap)
- Judge decides winner
- Update ELO

### 7. Match Volume

- ~50–100 matches per model
- Enough to study convergence behavior

## Reliability & Stability Analysis (Where the Paper Wins)

### 8. Convergence

- Rank correlation vs number of matches
- Identify stabilization thresholds

### 9. Bootstrap Analysis

- Resample matches
- Compute rank confidence intervals

### 10. Sensitivity Tests

- Topic subsampling
- Judge re-evaluation
- Prompt perturbations

**Expected finding:**
Rankings that look stable may still have overlapping confidence intervals.

## Prompt Sensitivity Study

### 11. Variables

- Structured vs freeform debate prompts
- Explicit clash instructions vs none
- Evidence-first vs narrative-first

### 12. Outputs

- Win-rate deltas
- Rank shifts
- Category-level effects

**Interpretation:**
Prompt choice is a major confounder in debate benchmarks.

## Metrics (Deliberately Simple)

- Win rate
- ELO
- Rank correlation (Spearman/Kendall)
- Confidence intervals

No embedding similarity as a primary metric.

## Limitations (Explicit)

- AI-only evaluation
- Single debate format
- Judge-dependent outcomes
- No claim of human alignment

## Deliverables

- DebateBench protocol
- JudgeBench protocol
- Leaderboard + confidence plots
- Open-source repo
- Reproducible pipeline

## Narrative Framing (Very Important)

**This is not:**
"Here is the best debate model."

**This is:**
"Here is why benchmarking debate is hard—and how to do it responsibly."

That framing is what gives this spotlight-level potential.

If you want next, I recommend doing one of these (highest leverage):
1. Draft the "Why Existing Evaluation Fails" section
2. Write the Contributions section exactly as it would appear in the paper
3. Design the key negative-result experiment that anchors the paper

Tell me which one you want to do next.

## Future

Get a ground truth judge (perfect judge) to get a similarity test

