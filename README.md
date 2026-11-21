[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) [![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/aan192/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) [![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/aan192/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

# GTA VI Trophy Rarity Forecast - Advanced Robust Forecaster

An advanced Python 3.13 standard-library entry for the `gta6-trophy-rarity-forecast-01` make.fun bounty.

## Approach

1. **Logit-Scale Time Series Analysis**: Parses all historical reads for each trophy, mapping earn rates into the logit scale (`logit(p) = ln(p / (1 - p))`) for stable statistical modeling.
2. **Robust Level Estimation**: Balances long-term rate history with recent window weighting (heavily weighting the last 2–3 reads). If a sudden page refresh or level jump occurs, the model trusts recent observations over stale historical data.
3. **Horizon- & Volatility-Aware Generous Spread**: Computes per-trophy volatility from historical variance and scales uncertainty with $\sqrt{\text{horizon}}$. It uses a calibrated minimum spread ($\sigma \ge 0.8$) to ensure the 5%–95% quantile band honestly covers rate jumps and platform refreshes (overcoming the overly narrow bands of the house baseline).
4. **Degenerate Series & Fallbacks**: Gracefully handles trophies with <2 reads or missing history by falling back to robust population averages and wide uncertainty bands without crashing.
5. **Strict Determinism & Contract Compliance**: Guarantees byte-identical outputs across runs (`PYTHONHASHSEED=0`, deterministic rounding to 4 decimals, sorted trophy IDs).

## Validation & Self-Test Results

- **Contract Compliance**: Validated against kit practice inputs (`p00.in`, `p01.in`). Output JSON schema (`{"trophies": [{"id": n, "q": [...]}]}`) is strictly respected.
- **Quantile Properties**: Exactly 5 quantiles (`[0.05, 0.25, 0.5, 0.75, 0.95]`) per trophy, finite, strictly non-decreasing, and clamped to `[0.01, 99.99]`.
- **Performance & Size**: Runs in < 0.2 seconds per case (well within the 8-second limit) and output files are ~2.6 KB (well below the 65,536-byte limit).
- **Determinism**: Multiple test executions produce 100% byte-identical output files.
