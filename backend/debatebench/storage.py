"""Persistent storage for debates"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


DEBATES_DIR = Path(__file__).parent.parent.parent / "data" / "debates"


def ensure_debates_dir():
    """Ensure the debates directory exists"""
    DEBATES_DIR.mkdir(parents=True, exist_ok=True)


def get_debate_file_path(debate_id: str) -> Path:
    """Get the file path for a debate"""
    ensure_debates_dir()
    return DEBATES_DIR / f"{debate_id}.json"


def save_debate(debate_id: str, debate_data: Dict) -> None:
    """Save a debate to disk"""
    file_path = get_debate_file_path(debate_id)
    debate_data["saved_at"] = datetime.now().isoformat()

    with open(file_path, 'w') as f:
        json.dump(debate_data, f, indent=2, default=str)

    # Also save to JudgeBench if this is a JudgeBench debate
    try:
        from debatebench import judgebench
        if judgebench.is_judgebench_debate(debate_id):
            judgebench_file = judgebench.JUDGEBENCH_DEBATES_DIR / f"{debate_id}.json"
            judgebench.ensure_judgebench_dirs()
            with open(judgebench_file, 'w') as f:
                json.dump(debate_data, f, indent=2, default=str)
    except:
        pass  # Silently fail if judgebench is not available


def load_debate(debate_id: str) -> Optional[Dict]:
    """Load a debate from disk"""
    file_path = get_debate_file_path(debate_id)
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def load_all_debates() -> Dict[str, Dict]:
    """Load all debates from disk"""
    ensure_debates_dir()
    debates = {}
    
    if not DEBATES_DIR.exists():
        return debates
    
    for file_path in DEBATES_DIR.glob("*.json"):
        try:
            debate_id = file_path.stem
            with open(file_path, 'r') as f:
                debate_data = json.load(f)
                debates[debate_id] = debate_data
        except (json.JSONDecodeError, IOError):
            continue
    
    return debates


def delete_debate(debate_id: str) -> bool:
    """Delete a debate from disk"""
    file_path = get_debate_file_path(debate_id)
    
    if file_path.exists():
        try:
            file_path.unlink()
            return True
        except IOError:
            return False
    
    return False


