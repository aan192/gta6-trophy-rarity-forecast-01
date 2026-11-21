"""GTA VI Trophy Rarity Forecast - Advanced Model (make.fun bounty)
Python 3.13, standard library only.
"""

import json
import math
import os
import sys
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]

def clamp(x: float) -> float:
    return min(99.99, max(0.01, x))

def logit(pct: float) -> float:
    return math.log(clamp(pct) / (100 - clamp(pct)))

def inverse_logit(lg: float) -> float:
    p = 100 / (1 + math.exp(-lg))
    return clamp(p)

def round4(x: float) -> float | int:
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value.is_integer() else value

def forecast_trophy(history_rates, history_times, horizon_days, default_logit):
    """
    history_rates: list of float rates (or None) for this trophy across history reads
    history_times: list of float timestamps corresponding to history reads
    horizon_days: float horizon in days
    default_logit: fallback logit if no valid history
    """
    valid_pairs = [(t, r) for t, r in zip(history_times, history_rates) if r is not None]
    
    if not valid_pairs:
        m = default_logit
        # Generous spread for unobserved trophies with thin data
        s = max(1.2, 1.8 * math.sqrt(max(0.01, horizon_days)))
    else:
        times, rates = zip(*valid_pairs)
        logits = [logit(r) for r in rates]
        
        n = len(logits)
        # Thin data penalty / uncertainty boost for few reads
        thin_factor = 1.0 + (2.0 / math.sqrt(n)) if n < 5 else 1.0
        
        if n == 1:
            m = logits[0]
            s = max(1.0, 1.4 * thin_factor * math.sqrt(max(0.01, horizon_days)))
        else:
            recent_logits = logits[-3:] if n >= 3 else logits[-2:]
            recent_mean = sum(recent_logits) / len(recent_logits)
            long_mean = sum(logits) / n
            
            mean_lg = sum(logits) / n
            variance = sum((l - mean_lg) ** 2 for l in logits) / n
            std_lg = math.sqrt(variance)
            
            # Robust blend of recent and long term, leaning on recent if sparse
            weight_recent = 0.8 if n < 5 else 0.75
            m = weight_recent * recent_mean + (1 - weight_recent) * long_mean
            
            vol_factor = max(0.5, std_lg)
            # Generous volatility and horizon-aware spread with thin data robustness
            s = max(0.9, (0.7 + 0.5 * vol_factor) * thin_factor * math.sqrt(max(0.01, horizon_days)))

    q_vals = []
    for z in Z:
        q = inverse_logit(m + z * s)
        q_vals.append(q)
    
    # Ensure non-decreasing
    for i in range(1, len(q_vals)):
        if q_vals[i] < q_vals[i-1]:
            q_vals[i] = q_vals[i-1]
            
    return [round4(q) for q in q_vals]

def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    
    history = case.get("history", [])
    horizon_days = case.get("horizon_minutes", 90) / 1440.0
    
    history_times = []
    for h in history:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(h["at"].replace("Z", "+00:00"))
            t = dt.timestamp() / 3600.0
        except Exception:
            t = float(len(history_times))
        history_times.append(t)
        
    all_last_logits = []
    if history:
        last_rates = history[-1].get("rates", [])
        for r in last_rates:
            if r is not None:
                all_last_logits.append(logit(r))
    default_logit = sum(all_last_logits) / len(all_last_logits) if all_last_logits else logit(1.0)
    
    trophies = case["trophies"]
    rows = []
    
    for i, trophy in enumerate(trophies):
        history_rates = [h["rates"][i] if i < len(h.get("rates", [])) else None for h in history]
        q = forecast_trophy(history_rates, history_times, horizon_days, default_logit)
        rows.append({"id": trophy["id"], "q": q})
        
    return {"trophies": rows}

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    in_files = sorted(INPUT_DIR.glob("*.in"))
    if not in_files:
        print(f"Warning: No *.in files found in {INPUT_DIR}", file=sys.stderr)
    for path in in_files:
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        out_path = OUTPUT_DIR / f"{path.stem}.out"
        out_path.write_text(json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
