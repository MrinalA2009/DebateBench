# JudgeBench: A Meta-Evaluation Framework for Selecting Stable AI Debate Judges

## Abstract

We present JudgeBench, a systematic meta-evaluation framework designed to identify the most stable and consistent AI model configurations for judging competitive debates. Through controlled experimentation across multiple judge models, prompting strategies, and debate instances, we quantify judge reliability using metrics including winner flip rate, score variance, confidence stability, and side bias. Our methodology enables evidence-based selection of judge configurations for large-scale debate benchmarks, ensuring fair and reproducible evaluation of debating AI systems.

---

## 1. Introduction

### 1.1 Motivation

AI-generated debates present unique evaluation challenges. Unlike traditional NLP tasks with ground-truth labels, debate quality assessment requires nuanced judgment of argumentation, evidence use, logical reasoning, and persuasive communication. The choice of judge model and prompting strategy can significantly impact evaluation outcomes, yet prior work lacks systematic approaches for selecting stable judge configurations.

### 1.2 Research Questions

1. Which AI models provide the most consistent debate judgments across repeated evaluations?
2. How sensitive are different models to prompt variation in debate judging?
3. What metrics best capture judge stability and reliability?
4. How can we systematically select optimal judge configurations for debate benchmarks?

### 1.3 Contributions

- **Systematic Meta-Evaluation Framework**: A reproducible methodology for evaluating debate judges
- **Comprehensive Stability Metrics**: Multi-dimensional assessment of judge reliability
- **Controlled Experimental Design**: Fixed debate set with paired model assignments
- **Practical Selection Criteria**: Evidence-based ranking of judge configurations

---

## 2. Methodology

### 2.1 Debate Generation

#### 2.1.1 Topic Selection

We curated 25 debate topics spanning 10 distinct categories to ensure topical diversity:

| Category | Topic Count | Examples |
|----------|-------------|----------|
| Technology & AI | 3 | AI regulation, facial recognition bans |
| Health & Bioethics | 3 | Telemedicine, assisted suicide |
| Society & Culture | 3 | Gender identity protection, gambling bans |
| Law & Justice | 3 | Gun regulation, police defunding |
| Environment & Climate | 3 | Private jet bans, deep-sea mining |
| Politics & Government | 2 | Voting age, nationalism |
| Economy & Labor | 2 | Tipping culture, gender pay gap |
| Education | 2 | Programming education, bilingual education |
| Space & Future | 2 | Celestial ownership, simulation hypothesis |
| International Relations | 2 | Diplomatic immunity, tourism restrictions |

**Topic Selection Criteria**:
- Balanced representation across domains
- Resolutions with clear PRO/CON positions
- Contemporary relevance and real-world significance
- Adequate complexity for substantive argumentation

#### 2.1.2 Model Pairs

We selected three model pairs representing different capability tiers:

| Pair | PRO Model | CON Model | Debate Count |
|------|-----------|-----------|--------------|
| 1 | GPT-4o-mini | LLaMA-3.3-70B | 8 |
| 2 | GPT-4o-mini | Gemini-2.5-Flash | 8 |
| 3 | LLaMA-3.3-70B | Gemini-2.5-Flash | 9 |

**Total**: 25 debate topics

**Model Selection Rationale**:

The three models were selected to ensure **competitive balance** and **ecosystem diversity**:

**Balanced Performance**:
- All three models demonstrate comparable debating capabilities in preliminary testing
- No single model dominates across all topic categories
- Performance parity ensures judges evaluate meaningful argumentation differences rather than capability gaps
- Competitive debates better test judge discrimination ability than mismatched contests

**Open-Source vs. Commercial Diversity**:
- **GPT-4o-mini (OpenAI)**: Commercial flagship - efficient reasoning, strong analytical capabilities
- **LLaMA-3.3-70B (Meta)**: Open-source alternative - community-accessible, transparent architecture, balanced performance
- **Gemini-2.5-Flash (Google)**: Commercial competitor - fast inference, competitive quality, different training paradigm

**Why This Matters**:
1. **Generalizability**: Results apply across different model architectures and training approaches
2. **Accessibility**: Including open-source ensures reproducibility without proprietary dependencies
3. **Robustness**: Diverse training methods test judge stability across varied argumentation styles
4. **Fairness**: Balanced capabilities prevent systematic winner bias that could mask judge instability

This configuration ensures JudgeBench measures genuine judge reliability rather than model-specific evaluation patterns.

#### 2.1.3 Paired Debate Design

For each topic, we generate **two debate instances**:
1. **Original Assignment**: Model A (PRO) vs Model B (CON)
2. **Flipped Assignment**: Model B (PRO) vs Model A (CON)

This paired design controls for:
- Position bias (PRO advantage/disadvantage)
- Model-specific argumentation styles
- Order effects in sequential speeches

**Total Debate Instances**: 25 topics × 2 assignments = **50 debates**

#### 2.1.4 Debate Structure

Each debate follows a standardized format:

| Speech Type | Word Limit | Purpose |
|-------------|------------|---------|
| PRO Constructive | 300 words | Initial argument presentation |
| CON Constructive | 300 words | Counter-argument and refutation |
| PRO Rebuttal | 250 words | Response to CON arguments |
| CON Rebuttal | 250 words | Response to PRO arguments |
| PRO Summary | 200 words | Final synthesis and impact |
| CON Summary | 200 words | Final synthesis and impact |

**Total**: 6 speeches per debate

**Debate Generation Parameters**:
- **Temperature**: 0.1 (high consistency, minimal randomness for reproducible arguments)
- **Prompt Style**: "analytical" (emphasizing logical reasoning and structured argumentation)
- **Turn Structure**: Sequential speech generation with full context

#### 2.1.5 Prompt Style Selection

We selected the **"analytical"** prompt style for debate generation to ensure consistent, logic-focused argumentation across all debates.

**Prompt Style Options**:

| Style | Characteristics | Trade-offs |
|-------|----------------|------------|
| **Analytical** | Structured reasoning, evidence-based claims, logical flow | More formal, less creative but highly consistent |
| Creative | Diverse rhetorical strategies, narrative elements, varied tone | More engaging but less predictable across runs |
| Persuasive | Emotional appeals, rhetorical devices, audience-focused | Effective but introduces stylistic variance |
| Technical | Domain-specific terminology, detailed analysis, precision | Deep but potentially less accessible |

**Rationale for Analytical Style**:
1. **Consistency**: Minimizes stylistic variance that could confound judge evaluation
2. **Logical Structure**: Facilitates fair comparison across different model capabilities
3. **Reproducibility**: Structured arguments are more stable across temperature settings
4. **Judge Compatibility**: Aligns with rubric criteria emphasizing argument quality and logical reasoning

This choice ensures that measured judge instability reflects genuine evaluation inconsistency rather than debate content randomness.

### 2.2 Judge Configurations

#### 2.2.1 Judge Models

We evaluate three judge models selected for distinct characteristics:

1. **anthropic/claude-sonnet-4.5**: Frontier reasoning, nuanced analysis
2. **x-ai/grok-4.1-fast**: Fast inference, efficiency-focused
3. **openai/gpt-4o-mini**: Balanced cost-performance ratio

#### 2.2.2 Judge Prompts

We systematically vary prompting strategies to measure sensitivity:

**P0 - Baseline Prompt (Holistic Evaluation)**
```
Evaluates debates using a comprehensive rubric covering:
- Argument Quality: Logical structure, claim support
- Evidence Use: Source quality, integration
- Clash: Direct engagement with opposing arguments
- Weighing: Comparative impact analysis

Outputs structured JSON with scores (0-10), winner determination,
confidence level (0-1), and reasoning.
```

**P1 - Procedural Prompt (Two-Stage Reasoning)**
```
Implements explicit two-stage evaluation:
Stage 1: Argument Survival - Identify which arguments withstand scrutiny
Stage 2: Comparative Evaluation - Weigh surviving arguments for impact

Emphasizes systematic analysis and transparent decision-making.
```

**P2 - Weighing Emphasis Prompt**
```
Prioritizes impact weighing and comparative analysis:
- Focuses on argument magnitude over quantity
- Emphasizes real-world implications
- Requires explicit comparative reasoning

Designed to test sensitivity to evaluation criteria emphasis.
```

**Total Judge Configurations**: 3 models × 3 prompts = **9 configurations**

#### 2.2.3 Evaluation Parameters

- **Runs per Debate**: 3 (measuring within-configuration stability)
- **Judge Temperature**: 0.1 (promoting consistency)
- **Output Format**: Structured JSON with enforced schema

**Total Judgments**: 50 debates × 3 runs × 9 configurations = **1,350 judgments**

---

## 3. Stability Metrics

### 3.1 Winner Flip Rate

**Definition**: Proportion of debates where repeated judgments by the same configuration produce different winners.

**Formula**:
```
flip_rate = (debates_with_winner_disagreement) / (total_debates)
```

**Interpretation**:
- **Low flip rate** (< 10%): Highly consistent winner determination
- **Medium flip rate** (10-30%): Moderate consistency, acceptable for most use cases
- **High flip rate** (> 30%): Unreliable, significant randomness in outcomes

**Importance**: Most critical metric - winner determination is the primary evaluation outcome.

### 3.2 Score Variance

**Definition**: Average variance of rubric scores across repeated evaluations of the same debate.

**Calculation**:
For each debate and each scoring category (Argument Quality, Evidence, Clash, Weighing):

```
For each side (PRO, CON):
  scores = [score_run1, score_run2, score_run3]
  variance = Var(scores)

category_variance = mean(variance_PRO, variance_CON)
```

**Aggregation**:
```
score_variance = {
  "argument_quality": mean_variance_across_debates,
  "evidence": mean_variance_across_debates,
  "clash": mean_variance_across_debates,
  "weighing": mean_variance_across_debates
}
```

**Interpretation**:
- Measures fine-grained consistency in evaluation criteria
- High variance suggests unstable scoring even when winner is consistent
- Category-specific variance reveals which aspects are most stable

### 3.3 Confidence Variance

**Definition**: Variance in judge-reported confidence levels across repeated evaluations.

**Formula**:
```
For each debate:
  confidences = [confidence_run1, confidence_run2, confidence_run3]
  variance = Var(confidences)

confidence_variance = mean(variances_across_debates)
```

**Interpretation**:
- Measures stability of judge certainty
- High variance suggests uncertainty about decision difficulty
- Low variance indicates consistent perception of debate closeness

### 3.4 Side Bias

**Definition**: Deviation from expected 50-50 split in PRO/CON wins across all judgments.

**Formula**:
```
total_pro_wins = count(winner == "PRO")
total_con_wins = count(winner == "CON")
total_judgments = total_pro_wins + total_con_wins

pro_rate = total_pro_wins / total_judgments
side_bias = |pro_rate - 0.5|
```

**Interpretation**:
- **Low bias** (< 5%): Fair evaluation, no systematic position preference
- **Medium bias** (5-15%): Slight preference, may indicate prompt/model characteristics
- **High bias** (> 15%): Significant unfairness, systematic position advantage

**Note**: Non-zero bias is acceptable if debates genuinely favor one side on average, but systematic bias across diverse topics indicates judge unreliability.

### 3.5 Prompt Sensitivity

**Definition**: Agreement rate between different prompts using the same judge model.

**Calculation**:
For each model, comparing all prompt pairs (P0-P1, P0-P2, P1-P2):

```
common_debates = debates_judged_by_both_prompts
disagreements = count(winner_prompt1 != winner_prompt2)
disagreement_rate = disagreements / common_debates

score_deltas = |scores_prompt1 - scores_prompt2| across categories
avg_score_delta = mean(score_deltas)
```

**Output**:
```
{
  "disagreement_rate": fraction of winner disagreements,
  "avg_score_delta": mean absolute difference in scores
}
```

**Interpretation**:
- High prompt sensitivity suggests fragile evaluation process
- Models with low sensitivity are more robust to prompt variation

---

## 4. Composite Stability Score

### 4.1 Weighted Ranking Formula

We combine metrics into a single **Instability Score** (lower is better):

```python
instability_score = (
    3.0 * flip_rate +
    1.0 * mean(score_variance_across_categories) +
    0.5 * confidence_variance +
    2.0 * side_bias
)
```

### 4.2 Weight Rationale

| Metric | Weight | Justification |
|--------|--------|---------------|
| Flip Rate | 3.0 | Most critical - directly impacts benchmark validity |
| Score Variance | 1.0 | Important for fine-grained analysis, secondary to winner |
| Confidence Variance | 0.5 | Informative but not outcome-determinative |
| Side Bias | 2.0 | Fairness is essential, systematic bias undermines validity |

### 4.3 Ranking Procedure

1. Compute all metrics for each of 9 judge configurations
2. Calculate composite instability score
3. Rank configurations by score (ascending)
4. **Lowest score** = most stable configuration → **recommended judge**

---

## 5. Data Storage and Reproducibility

### 5.1 Directory Structure

```
data/
├── debates/                    # All generated debates (main storage)
│   └── {debate_id}.json       # Full debate with speeches
├── judgebench/
│   ├── debate_ids.json        # List of JudgeBench debate IDs
│   ├── debates/               # JudgeBench debate copies with transcripts
│   │   └── {debate_id}.json
│   ├── results/               # Judge evaluation results
│   │   └── {judge_config}/
│   │       └── {debate_id}_run{N}.json
│   └── config.json            # Experiment configuration
```

### 5.2 Data Formats

#### Debate Instance
```json
{
  "id": "uuid",
  "resolution": "Resolved: ...",
  "pro_model": "openai/gpt-4o-mini",
  "con_model": "meta-llama/llama-3.3-70b-instruct",
  "temperature": 0.1,
  "prompt_style": "analytical",
  "status": "complete",
  "speeches": [
    {
      "side": "PRO",
      "speech_type": "pro_constructive",
      "content": "..."
    }
  ],
  "pair_id": "uuid_of_flipped_debate",
  "model_assignment": "original",
  "created_at": 1234567890.123
}
```

#### Judgment Result
```json
{
  "debate_id": "uuid",
  "judge_model": "anthropic/claude-sonnet-4.5",
  "judge_prompt": "p0",
  "run_number": 0,
  "judgment": "full text response",
  "winner": "PRO",
  "scores": {
    "argument_quality": {"PRO": 8.5, "CON": 7.0},
    "evidence": {"PRO": 8.0, "CON": 7.5},
    "clash": {"PRO": 7.5, "CON": 8.0},
    "weighing": {"PRO": 8.5, "CON": 7.0}
  },
  "confidence": 0.75,
  "short_reason": "...",
  "timestamp": 1234567890.123
}
```

### 5.3 Reproducibility Guarantees

- **Fixed Debate Set**: All judges evaluate identical debates
- **Controlled Randomness**: Seeded generation ensures reproducibility
- **Version Control**: Model versions, prompt versions logged
- **Complete Transcripts**: Full debate and judgment text preserved
- **Metadata Tracking**: Temperature, timestamps, configurations recorded

---

## 6. Experimental Controls

### 6.1 Controlled Variables

| Variable | Value | Control Method |
|----------|-------|----------------|
| Debate Topics | 25 fixed | Pre-selected from curated list |
| Model Pairs | 3 pairs | Fixed assignment across experiments |
| Debate Structure | 6 speeches | Enforced format with word limits |
| Debate Temperature | 0.1 | Constant across all debates for high consistency |
| Judge Temperature | 0.1 | Constant across all judgments |
| Runs per Debate | 3 | Fixed repetition for variance measurement |

### 6.2 Randomness Sources

**Controlled Randomness** (acceptable):
- Model sampling within temperature bounds
- Inherent model stochasticity at T=0.1

**Uncontrolled Randomness** (minimized):
- API latency variations (logged but not controlled)
- Model version updates (mitigated by version pinning)

### 6.3 Potential Confounds

| Confound | Mitigation Strategy |
|----------|---------------------|
| Topic difficulty variance | Diverse topic selection, statistical aggregation |
| Model capability differences | Paired design controls for model-specific effects |
| Debate length variation | Word limits enforce comparable effort |
| Position bias | Flipped debates measure and control for bias |
| Temporal effects | All judgments collected in similar timeframe |

---

## 7. Statistical Analysis Plan

### 7.1 Primary Analysis

**Objective**: Identify judge configuration with lowest instability score

**Method**:
1. Compute all metrics for each configuration
2. Calculate composite instability scores
3. Rank configurations
4. Report confidence intervals via bootstrap resampling

### 7.2 Secondary Analyses

**Model Comparison**:
- ANOVA testing for significant differences between models
- Post-hoc pairwise comparisons (Bonferroni corrected)

**Prompt Sensitivity**:
- Within-model prompt variation analysis
- Interaction effects (model × prompt)

**Metric Correlations**:
- Correlation matrix of stability metrics
- Principal component analysis of metric space

### 7.3 Validation Approaches

**Internal Validation**:
- Bootstrap resampling for ranking stability (1000 iterations)
- Leave-one-debate-out cross-validation
- Sensitivity analysis on metric weights

**Robustness Checks**:
- Alternative composite scoring formulas
- Threshold sensitivity (e.g., flip rate > X%)
- Subset analysis (e.g., by topic category)

---

## 8. Limitations and Future Work

### 8.1 Current Limitations

1. **Limited Model Coverage**: 3 judge models (resource constraints)
2. **English-Only**: No multilingual debate evaluation
3. **Format Specificity**: Results may not generalize to other debate formats
4. **Temporal Snapshot**: Model capabilities evolve over time
5. **Prompt Space**: 3 prompts explore limited strategy space

### 8.2 Future Extensions

**Expanded Evaluation**:
- Additional judge models (GPT-4, Claude Opus, Gemini Pro)
- More prompt variations (chain-of-thought, few-shot examples)
- Larger debate set (100+ debates for greater statistical power)

**Alternative Metrics**:
- Inter-judge agreement (human-AI, AI-AI)
- Calibration analysis (confidence vs. accuracy)
- Robustness to adversarial debates

**Domain Generalization**:
- Cross-domain stability (STEM, humanities, policy)
- Format variations (parliamentary, LD, policy debate)
- Multilingual evaluation frameworks

**Longitudinal Studies**:
- Model version tracking over time
- Stability degradation analysis
- Prompt drift and adaptation

---

## 9. Ethical Considerations

### 9.1 Fairness

- Paired debate design ensures position fairness
- Side bias metric explicitly measures and reports unfairness
- Diverse topic selection prevents domain-specific bias

### 9.2 Transparency

- All prompts, models, and parameters publicly documented
- Complete debate transcripts and judgments preserved
- Methodology fully reproducible

### 9.3 Limitations Disclosure

- Statistical uncertainty quantified and reported
- Generalization boundaries clearly stated
- Model-specific biases acknowledged

### 9.4 Responsible Use

This framework is intended for:
- Benchmark development and validation
- AI system evaluation and comparison
- Research on AI reasoning and judgment

**Not intended for**:
- High-stakes decision-making without human oversight
- Replacement of human judgment in critical contexts
- Evaluation of human debaters (out of scope)

---

## 10. Implementation Details

### 10.1 Software Stack

- **Backend**: Python 3.10+, FastAPI
- **Frontend**: React 18, Axios
- **Storage**: JSON file-based (PostgreSQL for production scale)
- **API**: OpenRouter for unified model access
- **Analysis**: NumPy, pandas for metrics computation

### 10.2 Computational Requirements

- **Debate Generation**: ~25 debates × 2 = 50 debates @ ~2-5 min each = **4-8 hours**
- **Judge Evaluation**: 1,350 judgments @ ~30-60 sec each = **11-22 hours**
- **Total Runtime**: ~15-30 hours (parallelizable)
- **Storage**: ~100 MB for full dataset
- **Compute**: CPU-based, API-bound (no GPU required)

### 10.3 Cost Estimates

| Component | API Calls | Est. Cost (USD) |
|-----------|-----------|-----------------|
| Debate Generation (6 speeches × 50) | 300 | $3-5 |
| Judge Evaluations (1,350) | 1,350 | $8-15 |
| **Total** | 1,650 | **$11-20** |

*Note: Costs vary by model pricing and usage tier*

---

## 11. Results Template

### 11.1 Judge Configuration Rankings

| Rank | Configuration | Instability Score | Flip Rate | Side Bias | Score Var | Conf Var |
|------|---------------|-------------------|-----------|-----------|-----------|----------|
| 1 | TBD | TBD | TBD | TBD | TBD | TBD |
| 2 | TBD | TBD | TBD | TBD | TBD | TBD |
| ... | ... | ... | ... | ... | ... | ... |

### 11.2 Recommended Configuration

**Best Judge**: [To be determined from experimental results]

**Justification**:
- Lowest flip rate: X%
- Minimal side bias: Y%
- Stable scoring: variance = Z
- Robust to prompt variation

### 11.3 Key Findings

[To be populated after experiment completion]

1. **Model Comparison**:
2. **Prompt Sensitivity**:
3. **Metric Correlations**:
4. **Surprising Results**:

---

## 12. Conclusion

JudgeBench provides a systematic, reproducible framework for meta-evaluating AI debate judges. By measuring stability across multiple dimensions and controlling for debate content through paired designs, we enable evidence-based selection of judge configurations for large-scale debate benchmarks.

**Key Innovations**:
1. Multi-dimensional stability metrics beyond simple agreement
2. Controlled experimental design with paired debates
3. Composite scoring for practical selection decisions
4. Full transparency and reproducibility

**Impact**:
- Establishes best practices for debate benchmark construction
- Quantifies judge reliability for informed selection
- Provides reusable methodology for future judge evaluation

---

## References

### Debate Formats and Evaluation
- [To be added: Academic debate literature]
- [To be added: Competitive debate judging standards]

### AI Evaluation Methodologies
- [To be added: LLM-as-judge literature]
- [To be added: Benchmark design principles]

### Statistical Methods
- [To be added: Bootstrap resampling references]
- [To be added: Composite scoring approaches]

---

## Appendices

### Appendix A: Complete Topic List

1. Resolved: The voting age should be lowered to 16. (Politics & Government)
2. Resolved: Victims of crimes should have a say in the sentencing of offenders. (Law & Justice)
3. Resolved: Nationalism is a destructive force in modern politics. (Politics & Government)
4. Resolved: Telemedicine should replace most routine doctor visits. (Health & Bioethics)
5. Resolved: Police departments should be defunded and funds reallocated to social services. (Law & Justice)
6. Resolved: Gender identity should be protected under the law. (Society & Culture)
7. Resolved: Biological hacking and DIY gene editing should be strictly regulated. (Technology & AI)
8. Resolved: We are likely living in a computer simulation. (Space & Future)
9. Resolved: Private jets should be banned. (Environment & Climate)
10. Resolved: Tipping culture should be abolished in favor of higher service wages. (Economy & Labor)
11. Resolved: Computer programming should be a mandatory subject from primary school. (Education)
12. Resolved: Ownership of celestial bodies (moons, planets) should be illegal. (Space & Future)
13. Resolved: Social media algorithms should be subject to public audits. (Technology & AI)
14. Resolved: Gambling and lotteries should be banned. (Society & Culture)
15. Resolved: Bilingual education should be mandatory. (Education)
16. Resolved: Parents should be legally required to limit their children's screen time. (Technology & AI)
17. Resolved: The gender pay gap should be closed through government mandates. (Economy & Labor)
18. Resolved: All narcotics should be decriminalized and treated as a health issue. (Health & Bioethics)
19. Resolved: Diplomatic immunity should be limited. (International Relations & Defense)
20. Resolved: Religion does more harm than good in the modern world. (Society & Culture)
21. Resolved: Gun ownership should be strictly regulated. (Law & Justice)
22. Resolved: Countries should have the right to restrict tourism to protect their culture. (International Relations & Defense)
23. Resolved: Air travel should be rationed to reduce emissions. (Environment & Climate)
24. Resolved: Assisted suicide should be legalized for the terminally ill. (Health & Bioethics)
25. Resolved: Deep-sea mining should be prohibited. (Environment & Climate)

### Appendix B: Judge Prompt Full Text

**[P0, P1, P2 prompts to be attached as separate appendix files]**

### Appendix C: Sample Debate Transcript

**[Representative debate to be included for reference]**

### Appendix D: Statistical Analysis Code

**[Python code for metrics computation to be made available in repository]**

---

**Document Version**: 1.0
**Last Updated**: 2026-01-01
**Status**: Methodology Complete, Awaiting Experimental Results
