#!/usr/bin/env bash
# Copy the shareable research outputs from the `results` branch into research_data/.
# Raw market data (prices, quotes, news, 5-minute bars) is never copied: the data
# vendors' terms do not allow redistributing it. Re-run after new results arrive:
#     bash scripts/export_research_data.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch -q origin results
OUT=research_data
rm -rf "$OUT/studies" "$OUT/zoo" "$OUT/backtest"
mkdir -p "$OUT/studies" "$OUT/zoo/parts" "$OUT/backtest/charts"

# studies: every table and write-up except quote-level samples
EXCLUDE='^(spreads_raw|auction_raw)\.csv$|^run\.log$|^README\.md$'
for f in $(git ls-tree --name-only origin/results research/latest/); do
  b=$(basename "$f")
  [[ "$b" =~ $EXCLUDE ]] && continue
  git show "origin/results:$f" > "$OUT/studies/$b"
done
git show origin/results:research/latest/README.md > "$OUT/studies/ALL_STUDIES.md"

# model zoo
for f in README.md best_correlations.csv zoo_all_strategies.csv summary.json; do
  git show "origin/results:research/zoo/$f" > "$OUT/zoo/$f"
done
for f in $(git ls-tree --name-only origin/results research/zoo/parts/); do
  git show "origin/results:$f" > "$OUT/zoo/parts/$(basename "$f")"
done

# the reference backtest of the stock book (the latest clean-data run; the
# research studies use the same one), plus a one-line summary of every run
RUN=$(git ls-tree -d --name-only origin/results runs/ | grep clean-data | tail -1)
for f in $(git ls-tree -r --name-only origin/results "$RUN"); do
  rel=${f#"$RUN"/}
  [ "$rel" = "run.log" ] && continue
  mkdir -p "$OUT/backtest/$(dirname "$rel")"
  git show "origin/results:$f" > "$OUT/backtest/$rel"
done
echo "$RUN" > "$OUT/backtest/SOURCE_RUN.txt"
python - "$OUT/backtest/all_runs.csv" <<'PY'
import json, subprocess, sys
import pandas as pd
runs = subprocess.run(["git", "ls-tree", "-d", "--name-only", "origin/results", "runs/"],
                      capture_output=True, text=True, check=True).stdout.split()
rows = []
for r in runs:
    s = subprocess.run(["git", "show", f"origin/results:{r}/summary.json"], capture_output=True, text=True)
    if s.returncode == 0:
        rows.append({"run": r.split("/", 1)[1], **json.loads(s.stdout)})
pd.DataFrame(rows).to_csv(sys.argv[1], index=False)
PY
du -sh "$OUT"
