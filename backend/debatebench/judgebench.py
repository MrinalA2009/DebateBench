"""JudgeBench: Meta-evaluation system for judge selection"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np


JUDGEBENCH_DIR = Path(__file__).parent.parent.parent / "data" / "judgebench"
JUDGEBENCH_DEBATES_DIR = JUDGEBENCH_DIR / "debates"
JUDGEBENCH_RESULTS_DIR = JUDGEBENCH_DIR / "results"
JUDGEBENCH_CONFIG_FILE = JUDGEBENCH_DIR / "config.json"


def ensure_judgebench_dirs():
    """Ensure JudgeBench directories exist"""
    JUDGEBENCH_DIR.mkdir(parents=True, exist_ok=True)
    JUDGEBENCH_DEBATES_DIR.mkdir(parents=True, exist_ok=True)
    JUDGEBENCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_judgebench_config(config: Dict) -> None:
    """Save JudgeBench configuration"""
    ensure_judgebench_dirs()
    config["saved_at"] = datetime.now().isoformat()
    with open(JUDGEBENCH_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, default=str)


def load_judgebench_config() -> Optional[Dict]:
    """Load JudgeBench configuration"""
    if not JUDGEBENCH_CONFIG_FILE.exists():
        return None
    try:
        with open(JUDGEBENCH_CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_judgebench_debate_ids() -> List[str]:
    """Get list of JudgeBench debate IDs"""
    ensure_judgebench_dirs()
    ids_file = JUDGEBENCH_DIR / "debate_ids.json"

    if ids_file.exists():
        try:
            with open(ids_file, 'r') as f:
                data = json.load(f)
                return data.get("debate_ids", [])
        except (json.JSONDecodeError, IOError):
            pass
    return []


def is_judgebench_debate(debate_id: str) -> bool:
    """Check if a debate is part of JudgeBench"""
    return debate_id in get_judgebench_debate_ids()


def save_judgebench_debate_id(debate_id: str) -> None:
    """Save a debate ID to the JudgeBench set"""
    ensure_judgebench_dirs()
    ids_file = JUDGEBENCH_DIR / "debate_ids.json"

    # Load existing IDs
    existing_ids = get_judgebench_debate_ids()

    # Add new ID if not already present
    if debate_id not in existing_ids:
        existing_ids.append(debate_id)

    # Save updated list
    with open(ids_file, 'w') as f:
        json.dump({"debate_ids": existing_ids}, f, indent=2)


def save_judgebench_debate(debate_id: str, debate_data: Dict) -> None:
    """Save a JudgeBench debate with full data"""
    ensure_judgebench_dirs()

    # Save the debate ID
    save_judgebench_debate_id(debate_id)

    # Save the full debate data
    file_path = JUDGEBENCH_DEBATES_DIR / f"{debate_id}.json"
    with open(file_path, 'w') as f:
        json.dump(debate_data, f, indent=2, default=str)


def load_judgebench_debate(debate_id: str) -> Optional[Dict]:
    """Load a JudgeBench debate"""
    file_path = JUDGEBENCH_DEBATES_DIR / f"{debate_id}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def load_all_judgebench_debates() -> List[Dict]:
    """Load all JudgeBench debates"""
    ensure_judgebench_dirs()
    debates = []

    if not JUDGEBENCH_DEBATES_DIR.exists():
        return debates

    for file_path in JUDGEBENCH_DEBATES_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                debate_data = json.load(f)
                debates.append(debate_data)
        except (json.JSONDecodeError, IOError):
            continue

    return debates


def save_judgment_result(judge_config: str, debate_id: str, run_number: int, result: Dict) -> None:
    """Save a single judgment result"""
    ensure_judgebench_dirs()
    # Create directory for this judge config
    config_dir = JUDGEBENCH_RESULTS_DIR / judge_config
    config_dir.mkdir(parents=True, exist_ok=True)

    # Save result
    file_path = config_dir / f"{debate_id}_run{run_number}.json"
    result["saved_at"] = datetime.now().isoformat()
    with open(file_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)


def load_judgment_results(judge_config: str) -> Dict[str, List[Dict]]:
    """Load all judgment results for a judge configuration

    Returns:
        Dict mapping debate_id to list of judgment results
    """
    config_dir = JUDGEBENCH_RESULTS_DIR / judge_config
    if not config_dir.exists():
        return {}

    results = {}
    for file_path in config_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                result = json.load(f)
                debate_id = result.get("debate_id")
                if debate_id:
                    if debate_id not in results:
                        results[debate_id] = []
                    results[debate_id].append(result)
        except (json.JSONDecodeError, IOError):
            continue

    return results


def compute_flip_rate(results: Dict[str, List[Dict]]) -> float:
    """Compute winner flip rate across repeated runs

    Args:
        results: Dict mapping debate_id to list of judgment results

    Returns:
        Flip rate (proportion of debates with winner disagreement)
    """
    debates_with_flip = 0
    total_debates = 0

    for debate_id, judgments in results.items():
        if len(judgments) < 2:
            continue

        total_debates += 1
        winners = [j.get("winner") for j in judgments if j.get("winner")]

        if len(set(winners)) > 1:
            debates_with_flip += 1

    if total_debates == 0:
        return 0.0

    return debates_with_flip / total_debates


def compute_score_variance(results: Dict[str, List[Dict]]) -> Dict[str, float]:
    """Compute score variance across repeated runs

    Returns:
        Dict mapping category to average variance
    """
    categories = ["argument_quality", "evidence", "clash", "weighing"]
    variances = {cat: [] for cat in categories}

    for debate_id, judgments in results.items():
        if len(judgments) < 2:
            continue

        for category in categories:
            pro_scores = []
            con_scores = []

            for j in judgments:
                scores = j.get("scores", {}).get(category, {})
                if scores:
                    pro_scores.append(scores.get("PRO", 0))
                    con_scores.append(scores.get("CON", 0))

            if pro_scores:
                variances[category].append(np.var(pro_scores))
                variances[category].append(np.var(con_scores))

    # Average variance across debates
    avg_variances = {}
    for category, vars_list in variances.items():
        if vars_list:
            avg_variances[category] = float(np.mean(vars_list))
        else:
            avg_variances[category] = 0.0

    return avg_variances


def compute_confidence_variance(results: Dict[str, List[Dict]]) -> float:
    """Compute confidence score variance across repeated runs"""
    variances = []

    for debate_id, judgments in results.items():
        if len(judgments) < 2:
            continue

        confidences = [j.get("confidence", 0) for j in judgments if j.get("confidence") is not None]

        if len(confidences) >= 2:
            variances.append(np.var(confidences))

    if variances:
        return float(np.mean(variances))
    return 0.0


def compute_side_bias(results: Dict[str, List[Dict]]) -> float:
    """Compute side bias (deviation from 50-50 PRO/CON wins)

    Returns:
        Absolute deviation from 0.5
    """
    total_wins = {"PRO": 0, "CON": 0}

    for debate_id, judgments in results.items():
        for j in judgments:
            winner = j.get("winner")
            if winner in total_wins:
                total_wins[winner] += 1

    total = sum(total_wins.values())
    if total == 0:
        return 0.0

    pro_rate = total_wins["PRO"] / total
    return abs(pro_rate - 0.5)


def compute_prompt_sensitivity(all_results: Dict[str, Dict[str, List[Dict]]], judge_model: str) -> Dict:
    """Compute prompt sensitivity for a given judge model

    Args:
        all_results: Dict mapping judge_config to results dict
        judge_model: The judge model to analyze

    Returns:
        Dict with prompt sensitivity metrics
    """
    # Get results for this model across different prompts
    model_results = {}
    for config, results in all_results.items():
        if judge_model in config:
            # Extract prompt from config (format: "model_prompt")
            parts = config.split("_")
            if len(parts) >= 2:
                prompt = parts[-1]
                model_results[prompt] = results

    if len(model_results) < 2:
        return {"disagreement_rate": 0.0, "avg_score_delta": 0.0}

    # Compare P0 vs P1, P0 vs P2, P1 vs P2
    disagreements = []
    score_deltas = []

    prompts = list(model_results.keys())
    for i in range(len(prompts)):
        for j in range(i + 1, len(prompts)):
            p1, p2 = prompts[i], prompts[j]

            # Find common debates
            common_debates = set(model_results[p1].keys()) & set(model_results[p2].keys())

            for debate_id in common_debates:
                results_p1 = model_results[p1][debate_id]
                results_p2 = model_results[p2][debate_id]

                if results_p1 and results_p2:
                    # Compare first run from each
                    winner_p1 = results_p1[0].get("winner")
                    winner_p2 = results_p2[0].get("winner")

                    if winner_p1 and winner_p2:
                        if winner_p1 != winner_p2:
                            disagreements.append(1)
                        else:
                            disagreements.append(0)

                    # Compare scores
                    scores_p1 = results_p1[0].get("scores", {})
                    scores_p2 = results_p2[0].get("scores", {})

                    if scores_p1 and scores_p2:
                        for category in ["argument_quality", "evidence", "clash", "weighing"]:
                            s1 = scores_p1.get(category, {})
                            s2 = scores_p2.get(category, {})

                            if s1 and s2:
                                delta_pro = abs(s1.get("PRO", 0) - s2.get("PRO", 0))
                                delta_con = abs(s1.get("CON", 0) - s2.get("CON", 0))
                                score_deltas.append(delta_pro)
                                score_deltas.append(delta_con)

    return {
        "disagreement_rate": float(np.mean(disagreements)) if disagreements else 0.0,
        "avg_score_delta": float(np.mean(score_deltas)) if score_deltas else 0.0
    }


def compute_all_metrics(all_results: Dict[str, Dict[str, List[Dict]]]) -> Dict:
    """Compute all JudgeBench metrics for all judge configurations

    Returns:
        Dict with comprehensive metrics
    """
    metrics = {}

    for judge_config, results in all_results.items():
        config_metrics = {
            "judge_config": judge_config,
            "flip_rate": compute_flip_rate(results),
            "score_variance": compute_score_variance(results),
            "confidence_variance": compute_confidence_variance(results),
            "side_bias": compute_side_bias(results),
            "total_judgments": sum(len(judgments) for judgments in results.values()),
            "total_debates": len(results)
        }

        metrics[judge_config] = config_metrics

    return metrics


def rank_judge_configurations(metrics: Dict) -> List[Tuple[str, float]]:
    """Rank judge configurations by stability score

    Lower score is better (more stable)

    Returns:
        List of (judge_config, score) tuples sorted by score
    """
    # Weights for composite score
    w_flip = 3.0  # Winner flip is most important
    w_score_var = 1.0
    w_conf_var = 0.5
    w_bias = 2.0  # Side bias is important

    scores = []

    for judge_config, m in metrics.items():
        # Composite instability score
        avg_score_var = np.mean(list(m["score_variance"].values())) if m["score_variance"] else 0

        score = (
            w_flip * m["flip_rate"] +
            w_score_var * avg_score_var +
            w_conf_var * m["confidence_variance"] +
            w_bias * m["side_bias"]
        )

        scores.append((judge_config, float(score)))

    # Sort by score (lower is better)
    scores.sort(key=lambda x: x[1])

    return scores
