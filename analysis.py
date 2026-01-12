import json
import os
import glob
import statistics
from collections import defaultdict

def load_results(base_dir):
    # Structure: results[model][prompt][debate_id] = list of runs
    results = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    files = glob.glob(os.path.join(base_dir, "**/*.json"), recursive=True)
    
    for f in files:
        try:
            with open(f, 'r') as fd:
                data = json.load(fd)
                
            # Extract key info
            # Directory name is usually model_prompt, but let's rely on JSON fields if possible,
            # or parse directory if JSON is missing fields (though setup implies JSON has them).
            # The JSON has 'judge_model' and 'judge_prompt'.
            
            model = data.get('judge_model')
            prompt = data.get('judge_prompt')
            debate_id = data.get('debate_id')
            
            if not model or not prompt or not debate_id:
                # Fallback to path parsing if necessary
                # Path: data/judgebench/results/<config>/<filename>
                parts = f.split(os.sep)
                if len(parts) >= 2:
                    config = parts[-2]
                    # config is like "anthropic_claude-sonnet-4.5_p0"
                    # Try to split off the last part as prompt
                    if '_' in config:
                        prompt_guess = config.split('_')[-1]
                        model_guess = '_'.join(config.split('_')[:-1])
                        if not model: model = model_guess
                        if not prompt: prompt = prompt_guess

            if not model or not prompt:
                print(f"Skipping {f}: Could not determine model or prompt")
                continue
                
            # Normalize model name if needed (e.g., replace / with _)
            model = model.replace('/', '_')
            
            results[model][prompt][debate_id].append(data)
            
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    return results

def calculate_metrics(results):
    print("--- JudgeBench Analysis ---\n")
    
    # Store aggregated prompt stats for sensitivity analysis
    # model_prompt_stats[model][prompt][debate_id] = { avg_scores: {}, consensus_winner: str }
    model_prompt_stats = defaultdict(lambda: defaultdict(dict))

    for model in results:
        for prompt in results[model]:
            debates = results[model][prompt]
            
            # Metric 1: Winner Flip Rate
            # Count debates where winner differs across runs
            flip_count = 0
            total_debates = len(debates)
            
            # Metric 2: Score Variance
            all_score_variances = []
            
            # Metric 3: Confidence Variance
            all_conf_variances = []
            
            # Metric 4: Side Bias
            total_runs = 0
            pro_wins = 0
            
            for debate_id, runs in debates.items():
                # 1. Flip Rate
                winners = [r.get('winner') for r in runs if r.get('winner')]
                if len(set(winners)) > 1:
                    flip_count += 1
                
                # Determine consensus winner for this prompt (majority vote)
                if winners:
                    consensus_winner = max(set(winners), key=winners.count)
                else:
                    consensus_winner = None
                
                # 4. Side Bias
                for w in winners:
                    if w == 'PRO':
                        pro_wins += 1
                    total_runs += 1
                
                # 2. Score Variance
                # Categories: argument_quality, evidence, clash, weighing
                # Sides: PRO, CON
                # We need variance across runs for each (category, side) tuple
                
                # Initialize lists for this debate
                scores_lists = defaultdict(list)
                confidence_list = []
                
                for r in runs:
                    s = r.get('scores', {})
                    conf = r.get('confidence')
                    
                    if conf is not None:
                        confidence_list.append(float(conf))
                    
                    for cat in ['argument_quality', 'evidence', 'clash', 'weighing']:
                        if cat in s:
                            for side in ['PRO', 'CON']:
                                if side in s[cat]:
                                    scores_lists[(cat, side)].append(float(s[cat][side]))
                
                # Calculate variances for this debate
                debate_score_variances = []
                for key, vals in scores_lists.items():
                    if len(vals) > 1:
                        debate_score_variances.append(statistics.variance(vals))
                    elif len(vals) == 1:
                        debate_score_variances.append(0.0)
                        
                if debate_score_variances:
                    avg_debate_score_var = statistics.mean(debate_score_variances)
                    all_score_variances.append(avg_debate_score_var)
                
                # 3. Confidence Variance
                if len(confidence_list) > 1:
                    all_conf_variances.append(statistics.variance(confidence_list))
                elif len(confidence_list) == 1:
                    all_conf_variances.append(0.0)

                # Store stats for sensitivity analysis
                # Compute average score for each (cat, side)
                avg_scores = {}
                for key, vals in scores_lists.items():
                    if vals:
                        avg_scores[key] = statistics.mean(vals)
                
                model_prompt_stats[model][prompt][debate_id] = {
                    'consensus_winner': consensus_winner,
                    'avg_scores': avg_scores
                }

            # Aggregations for this config
            flip_rate = flip_count / total_debates if total_debates > 0 else 0
            
            avg_score_variance = statistics.mean(all_score_variances) if all_score_variances else 0
            avg_conf_variance = statistics.mean(all_conf_variances) if all_conf_variances else 0
            
            side_bias = (pro_wins / total_runs - 0.5) if total_runs > 0 else 0
            
            print(f"Configuration: {model} {prompt}")
            print(f"  Debates: {total_debates}")
            print(f"  1. Winner Flip Rate: {flip_rate:.2%}")
            print(f"  2. Score Variance:   {avg_score_variance:.4f}")
            print(f"  3. Confidence Var:   {avg_conf_variance:.4f}")
            print(f"  4. Side Bias:        {side_bias:.4f}")
            print("")

    # 5. Prompt Sensitivity
    print("--- Prompt Sensitivity (Inter-Prompt Analysis) ---")
    
    for model in model_prompt_stats:
        prompts = list(model_prompt_stats[model].keys())
        if len(prompts) < 2:
            continue
            
        print(f"\nModel: {model}")
        print(f"  Prompts compared: {prompts}")
        
        # We need to compare across prompts for the same debate
        # Find common debate IDs
        # Ideally all prompts have all debates
        all_debate_ids = set()
        for p in prompts:
            all_debate_ids.update(model_prompt_stats[model][p].keys())
            
        # Metrics
        winner_disagreements = 0
        total_comparable_debates = 0
        
        score_deltas = []
        
        for did in all_debate_ids:
            # Check if all prompts have this debate
            # To be strict, let's only compare if we have data for at least 2 prompts.
            # But the prompt asks to compare "across P0 vs P1 vs P2".
            # Let's collect winners and scores for available prompts
            
            active_prompts = [p for p in prompts if did in model_prompt_stats[model][p]]
            if len(active_prompts) < 2:
                continue
                
            total_comparable_debates += 1
            
            # Winner disagreement
            winners = [model_prompt_stats[model][p][did]['consensus_winner'] for p in active_prompts]
            # Filter None if any
            winners = [w for w in winners if w]
            
            if len(set(winners)) > 1:
                winner_disagreements += 1
                
            # Score deltas
            # Calculate max difference between any two prompts for each score category
            # Then average those max diffs
            
            # Gather scores: { (cat, side): [score_p0, score_p1, ...] }
            score_map = defaultdict(list)
            for p in active_prompts:
                p_scores = model_prompt_stats[model][p][did]['avg_scores']
                for k, v in p_scores.items():
                    score_map[k].append(v)
            
            debate_score_deltas = []
            for k, vals in score_map.items():
                if len(vals) > 1:
                    # Max difference in this category across prompts
                    diff = max(vals) - min(vals)
                    debate_score_deltas.append(diff)
            
            if debate_score_deltas:
                score_deltas.append(statistics.mean(debate_score_deltas))
                
        winner_disagreement_rate = winner_disagreements / total_comparable_debates if total_comparable_debates > 0 else 0
        avg_score_delta = statistics.mean(score_deltas) if score_deltas else 0
        
        print(f"  Winner Disagreement Rate: {winner_disagreement_rate:.2%}")
        print(f"  Average Score Delta:      {avg_score_delta:.4f}")

if __name__ == "__main__":
    base_dir = "data/judgebench/results"
    if os.path.exists(base_dir):
        data = load_results(base_dir)
        calculate_metrics(data)
    else:
        print(f"Directory not found: {base_dir}")
