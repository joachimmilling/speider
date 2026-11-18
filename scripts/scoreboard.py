"""Collect the headline number of every tested model into docs/scoreboard.md and append a row to docs/scoreboard_history.csv.

Reads the result files the analysis scripts write under data/. Run after any model change (scripts/run_all.py does it last).
"""
import csv
import datetime
import json
import subprocess
from pathlib import Path


def load(name):
    p = Path("data") / name
    return json.load(open(p)) if p.exists() else None


def main() -> None:
    sm, bv, sq, ts = load("result_site_models.json"), load("result_buy_verdict.json"), load("result_squad_model.json"), load("result_team_strength.json")
    rows = []          # (key, area, what, value, reference, note)
    if sm:
        v = sm["value"]
        rows += [("fee_miss", "Pricing", "Speider value: typical miss on fees not seen (2025-26)", v["speider_err"], f'third-party value {v["third_party_err"]}', f'n={v["n_test"]}, lower is better'),
                 ("fee_rank", "Pricing", "Speider value: rank correlation with fees", v["rank"], f'third-party value {v["rank_third_party"]}', ""),
                 ("fee_inside80", "Pricing", "Share of fees inside the 80 % range", v["inside_80"], "target 0.80", "")]
        if "speider_bias" in v: rows.append(("fee_bias", "Pricing", "Speider value: median prediction over fee (1 is unbiased)", v["speider_bias"], f'third-party value {v["third_party_bias"]}', "2025-26"))
        fo = load("result_fee_offset.json")
        if fo:
            k = "year-centred, bracket level"
            rows += [("fee_miss_rolling", "Pricing", "Speider value: typical miss, six years each predicted from earlier years (2021-26)", fo[k]["pooled"]["miss"], f'third-party value {fo["market value alone"]["pooled"]["miss"]}, model before test 30 {fo["site model today"]["pooled"]["miss"]}', "lower is better"),
                     ("fee_miss_buyer", "Pricing", "Same, when the buying club is known", fo[k + " + buyer"]["pooled"]["miss"], f'without buyer {fo[k]["pooled"]["miss"]}', "not on the site yet")]
        if "tail_value" in sm: rows.append(("fee_miss_40m", "Pricing", "Miss on fees for players worth 40m+", sm["tail_value"]["err_with_tail"], f'trees alone {sm["tail_value"]["err_trees"]}', f'n={sm["tail_value"]["n_test_40m"]}'))
    if bv:
        r, vd, vl = bv["next_fee_rank"], bv["verdict"], bv["verdict_large"]
        rows += [("next_fee_rank", "Pricing", "Predicting the next fee: Speider outcome model (rank)", r["C2"], f'fee paid {r["fee"]}, third-party value {r["A"]}', "higher is better"),
                 ("verdict_cheap", "Pricing", "Buys judged cheapest: resale / fee (median)", vd[-1][2], f"dearest fifth {vd[0][2]}", f"n={vd[-1][1]}"),
                 ("verdict_cheap_large", "Pricing", "Same, largest third of fees", vl[-1][2], f"dearest fifth {vl[0][2]}", f"n={vl[-1][1]}"),
                 ("flag_top", "Pricing", "Speider above market value, top fifth: next fee vs typical", bv["flag"]["top"], f'bottom fifth {bv["flag"]["bottom"]}', f'n={bv["flag"]["n"]}')]
    if sq:
        o = sq["out_of_time"]
        rows += [("squad_corr", "Squads", "Squad model: correlation with goal difference, seasons not seen", o["xi+depth+age + last season"]["corr"], f'last season only {o["last season only"]["corr"]}', f'n={sq["n_test"]}'),
                 ("squad_r2", "Squads", "Squad model: explained share", o["xi+depth+age + last season"]["r2"], f'value and level of the eleven {o["xi_value+level"]["r2"]}', ""),
                 ("squad_attr_r2", "Squads", "Same with the seven attributes added", o["xi+depth+age+attributes + last season"]["r2"], "no gain = attributes add nothing", "")]
    if ts:
        c = ts["corr_with_goal_difference"]
        rows.append(("xi_level_corr", "Squads", "Level of the best eleven alone: correlation with goal difference", c["level"], f'value of top eleven {c["value"]}, last season {c["gd_prev"]}', f'n={ts["n_all_three"]}'))
    fa = load("result_form_adjust.json")
    if fa:
        n = fa["nowcast"]
        rows.append(("nowcast_r2", "Pricing", "Form nowcast: explained share of value change during a season", n["plus the season"]["r2"], f'age and value {n["age and value"]["r2"]}', f'n={n["n_test"]}'))
        m_ = fa["fees"]["miss"]
        rows.append(("midseason_miss", "Pricing", "Miss on mid-season fees, site model", m_["A site model"]["running_season"], f'with form line {m_["C1 two-input line"]["running_season"]}, with nowcast {m_["C2 scaled nowcast"]["running_season"]}', f'n={fa["fees"]["n_test_running"]}, form not adopted'))
    sl = load("result_form_slope.json")
    if sl: rows.append(("form_slope", "Pricing", "Form slope in the price (fee above model per unit of form excess)", sl["slope"], f'90 % interval {sl["slope_90"][0]} to {sl["slope_90"][1]}', f'mid-season miss {sl["miss"]["site_model"]["running"]} -> {sl["miss"]["with_slope"]["running"]}, n={sl["n_test_running"]}'))
    ij, lb = load("result_injury.json"), load("result_lineup_balance.json")
    if ij: rows.append(("absent_next_rank", "Pricing", "Predicting next season's share out of the squad (rank)", ij["a"]["absent_next"]["plus out of squad, bench, listed injured"], f'minutes and age {ij["a"]["absent_next"]["minutes and age"]}', f'n={ij["a"]["n_test"]}'))
    if lb: rows.append(("match_r2", "Squads", "Match goal difference explained by both elevens' quality", lb["ridge"]["1 quality of both elevens"]["r2"], f'with attribute means {lb["ridge"]["2 plus seven attribute means"]["r2"]}, with balance terms {lb["ridge"]["3 plus lowest attribute and spread"]["r2"]}', f'n={lb["n_test"]}'))
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    today = datetime.date.today().isoformat()
    md = ["# Scoreboard", "", f"Rebuilt {today} at commit `{commit}` by `scripts/scoreboard.py`. History: `docs/scoreboard_history.csv`.", "",
          "| Area | Measure | Now | Reference | Note |", "|---|---|---|---|---|"]
    md += [f"| {a} | {w} | **{v}** | {ref} | {n} |" for _, a, w, v, ref, n in rows]
    hist = Path("docs/scoreboard_history.csv")
    prev = list(csv.DictReader(open(hist))) if hist.exists() else []
    now = dict(date=today, commit=commit, **{k: v for k, _, _, v, _, _ in rows})
    if prev:
        last = prev[-1]; moved = [(k, last.get(k), str(now[k])) for k in now if k not in ("date", "commit") and last.get(k) not in (None, "", str(now[k]))]
        md += ["", "## Changed since the previous row", ""] + ([f"- `{k}`: {a} -> {b}" for k, a, b in moved] or ["Nothing."])
        if all(last.get(k) == str(now[k]) for k in now if k not in ("date", "commit")) : prev = prev[:-1] if last.get("commit") == commit else prev
    keys = list(dict.fromkeys([k for r_ in prev for k in r_] + list(now)))
    with open(hist, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(prev); w.writerow({k: now.get(k, "") for k in keys})
    Path("docs/scoreboard.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
