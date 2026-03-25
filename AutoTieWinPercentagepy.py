import requests
import time
import statistics
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv('TBA_API_KEY')
HEADERS = {'X-TBA-Auth-Key': API_KEY}

def analyze_2026_with_updates():
    events = requests.get("https://www.thebluealliance.com/api/v3/events/2026/keys", headers=HEADERS).json()

    results = {
        "total_ties": 0,
        "active_s1_wins": 0,
        "inactive_s1_wins": 0,
        "residuals": [],
        "all_auto_scores": [],
        "tied_auto_scores": [],
        "tied_match_keys": [],
    }
    total_events = len(events)
    print(f"Found {total_events} events")

    for i, event_key in enumerate(events):
        print(f"[{i+1}/{total_events}] Processing {event_key}...", end="\r")

        matches = requests.get(
            f"https://www.thebluealliance.com/api/v3/event/{event_key}/matches",
            headers=HEADERS
        ).json()
        time.sleep(0.025)

        if not isinstance(matches, list):
            continue

        for m in matches:
            breakdown = m.get('score_breakdown')
            if not breakdown:
                continue

            r_hub = breakdown['red'].get('hubScore', {})
            b_hub = breakdown['blue'].get('hubScore', {})

            red_auto = r_hub.get('autoCount', 0)
            blue_auto = b_hub.get('autoCount', 0)

            results["all_auto_scores"].append(red_auto)
            results["all_auto_scores"].append(blue_auto)

            if red_auto != blue_auto:
                continue

            results["tied_auto_scores"].append(red_auto)
            results["tied_match_keys"].append(m['key'])
            results["total_ties"] += 1
            winner = m.get('winning_alliance')

            # --- Residuals (tied matches only) ---
            for alliance_hub, label in [(r_hub, 'red'), (b_hub, 'blue')]:
                teleop_actual = alliance_hub.get('teleopCount', 0)
                shift_sum = (
                    alliance_hub.get('shift1Count', 0) +
                    alliance_hub.get('shift2Count', 0) +
                    alliance_hub.get('shift3Count', 0) +
                    alliance_hub.get('shift4Count', 0)
                )
                residual = teleop_actual - shift_sum
                if residual != 0:
                    results["residuals"].append({
                        "match": m['key'],
                        "alliance": label,
                        "teleop_actual": teleop_actual,
                        "shift_sum": shift_sum,
                        "residual": residual,
                        "transition": alliance_hub.get('transitionCount', 0),
                        "uncounted": alliance_hub.get('uncounted', 0)
                    })

            # --- Tiebreaker win counting ---
            red_active_s1 = r_hub.get('shift1Count', 0) > 0
            blue_active_s1 = b_hub.get('shift1Count', 0) > 0

            if winner == 'red':
                winning_alliance_active = red_active_s1
            elif winner == 'blue':
                winning_alliance_active = blue_active_s1
            else:
                continue

            if winning_alliance_active:
                results["active_s1_wins"] += 1
            else:
                results["inactive_s1_wins"] += 1

            print(
                f"\n[TIE] {m['key']} | AutoFuel={red_auto} | "
                f"RedActiveS1={red_active_s1} | BlueActiveS1={blue_active_s1} | Winner={winner}"
            )

    # --- Tiebreaker summary ---
    print("\n\n" + "=" * 50)
    print("FRC 2026: SHIFT ORDER TIEBREAKER IMPACT")
    print("=" * 50)
    n = results["total_ties"]
    if n > 0:
        active_rate = (results["active_s1_wins"] / n) * 100
        print(f"Total Auto Fuel Ties:              {n}")
        print(f"Win % for 'Active S1':             {active_rate:.2f}%")
        print(f"Win % for 'Inactive S1':           {100 - active_rate:.2f}%")
    else:
        print("No ties found in the data.")

    # --- Auto score distribution ---
    print("\n" + "=" * 50)
    print("AUTO SCORE DISTRIBUTION")
    print("=" * 50)
    all_scores = results["all_auto_scores"]
    tied_scores = results["tied_auto_scores"]

    if all_scores:
        pop_avg = sum(all_scores) / len(all_scores)
        pop_zeros = all_scores.count(0) / len(all_scores) * 100
        pop_std = statistics.stdev(all_scores)
        pop_max = max(all_scores)
        print(f"Population (all alliances):        n={len(all_scores)}")
        print(f"  Average auto score:              {pop_avg:.2f}")
        print(f"  Std deviation:                   {pop_std:.2f}")
        print(f"  Highest auto score:              {pop_max}")
        print(f"  % scoring zero:                  {pop_zeros:.1f}%")

    if tied_scores:
        tie_avg = sum(tied_scores) / len(tied_scores)
        tie_zeros = tied_scores.count(0) / len(tied_scores) * 100
        tie_std = statistics.stdev(tied_scores)
        tie_max = max(tied_scores)
        tie_max_match = results["tied_match_keys"][tied_scores.index(tie_max)]
        print(f"Tied matches only:                 n={len(tied_scores)}")
        print(f"  Average tied auto score:         {tie_avg:.2f}")
        print(f"  Std deviation:                   {tie_std:.2f}")
        print(f"  Highest tied auto score:         {tie_max} ({tie_max_match})")
        print(f"  % of ties that were 0-0:         {tie_zeros:.1f}%")

    # --- Residual summary ---
    print("\n" + "=" * 50)
    print("RESIDUAL ANALYSIS (tied matches only)")
    print("=" * 50)
    r = results["residuals"]
    if r:
        total_residual = sum(x["residual"] for x in r)
        avg_residual = total_residual / len(r)
        print(f"Tied alliances with nonzero residuals: {len(r)}")
        print(f"Average residual:                      {avg_residual:.3f} balls")
        print(f"Total residual across dataset:         {total_residual} balls")
    else:
        print("No residuals found — all teleopCounts match shift sums exactly.")

analyze_2026_with_updates()