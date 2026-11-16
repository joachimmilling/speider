"""Run the whole chain in order: frame, models, backtests, both site builds, scoreboard. Stops at the first failure.

python3 scripts/run_all.py                    everything
python3 scripts/run_all.py --from site_models start at a step
python3 scripts/run_all.py --list             show the steps
"""
import os
import subprocess
import sys
import time

STEPS = [
    ("wide_frame", ["python3", "analysis/build_wide_frame.py"], {}),
    ("dropout", ["python3", "analysis/dropout_career.py"], {}),
    ("site_models", ["python3", "analysis/site_models.py"], {}),
    ("buy_test", ["python3", "analysis/buy_verdict_backtest.py"], {}),
    ("team_strength", ["python3", "analysis/team_strength_backtest.py"], {}),
    ("squad_model", ["python3", "analysis/squad_model.py"], {}),
    ("form_fee", ["python3", "analysis/form_fee_test.py"], {}),
    ("site", ["python3", "scripts/build_site.py"], {"SITE_LOGOS": "1"}),
    ("site_pub", ["python3", "scripts/build_site.py"], {"SITE_OUT": "data/site_pub", "SITE_SHARDS": "32"}),
    ("scoreboard", ["python3", "scripts/scoreboard.py"], {}),
]


def main() -> None:
    names = [s[0] for s in STEPS]
    if "--list" in sys.argv: print("\n".join(names)); return
    start = names.index(sys.argv[sys.argv.index("--from") + 1]) if "--from" in sys.argv else 0
    for name, cmd, env in STEPS[start:]:
        t = time.time(); print(f"== {name}", flush=True)
        r = subprocess.run(cmd, env={**os.environ, "PYTHONPATH": "analysis", **env}, stdout=subprocess.DEVNULL if name != "scoreboard" else None)
        if r.returncode: sys.exit(f"{name} failed")
        print(f"   {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
