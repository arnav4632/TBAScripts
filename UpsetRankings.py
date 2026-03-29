import json
import csv
import os
from tqdm import tqdm

BAYESIAN_CONFIDENCE = 5  # Number of matches needed to fully trust a team's win rate

def run_analysis(year=2025, min_underdog_matches=2):
    filename = f"matches_{year}.json"

    if not os.path.exists(filename):
        print(f"Error: {filename} not found. Run your download script first!")
        return

    with open(filename, 'r') as f:
        matches = json.load(f)

    # team_stats dictionary: { team_number: [underdog_match_count, upset_win_count, total_match_count] }
    team_stats = {}

    print(f"Analyzing {len(matches)} local matches for {year}...")

    for m in tqdm(matches):
        # 1. Extract nested data from the Statbotics JSON structure
        result = m.get('result', {})
        pred = m.get('pred', {})
        alliances = m.get('alliances', {})

        winner = result.get('winner')
        red_win_prob = pred.get('red_win_prob')

        # Skip if match isn't finished or prediction is missing
        if not winner or red_win_prob is None:
            continue

        red_teams = alliances.get('red', {}).get('team_keys', [])
        blue_teams = alliances.get('blue', {}).get('team_keys', [])

        # Process Red Alliance
        for team in red_teams:
            if team not in team_stats: team_stats[team] = [0, 0, 0]  # [underdog_match_count, upset_win_count, total_match_count]
            team_stats[team][2] += 1  # Increment total match count
            if red_win_prob < 0.5:  # Red was the underdog
                team_stats[team][0] += 1
                if winner == 'red':
                    team_stats[team][1] += 1

        # Process Blue Alliance
        for team in blue_teams:
            if team not in team_stats: team_stats[team] = [0, 0, 0]
            team_stats[team][2] += 1  # Increment total match count
            if red_win_prob > 0.5:  # Blue was the underdog (Red > 50%)
                team_stats[team][0] += 1
                if winner == 'blue':
                    team_stats[team][1] += 1

    # 2. Format and Calculate Rankings

    # Calculate league-wide average underdog win rate for Bayesian weighting
    all_upset_wins = sum(r[1] for r in team_stats.values())
    all_underdog_matches = sum(r[0] for r in team_stats.values() if r[0] >= min_underdog_matches)
    league_avg_rate = all_upset_wins / all_underdog_matches if all_underdog_matches > 0 else 0

    upset_leaderboard = []
    for team, team_record in team_stats.items():
        underdog_match_count = team_record[0]
        upset_win_count = team_record[1]
        total_match_count = team_record[2]

        if underdog_match_count >= min_underdog_matches:
            underdog_match_win_rate_pct = round((upset_win_count / underdog_match_count) * 100, 2)
            upset_frequency_pct = round((upset_win_count / total_match_count) * 100, 2)
            bayesian_weighted_rate_pct = round(
                ((upset_win_count + BAYESIAN_CONFIDENCE * league_avg_rate) / (underdog_match_count + BAYESIAN_CONFIDENCE)) * 100, 2
            )

            upset_leaderboard.append({
                'Team': team,
                'Upset Win Count': upset_win_count,
                'Underdog Match Count': underdog_match_count,
                'Underdog Match Win Rate (%)': underdog_match_win_rate_pct,
                'Bayesian Weighted Rate (%)': bayesian_weighted_rate_pct,
                'Upset Frequency (%)': upset_frequency_pct,
                'Total Match Count': total_match_count
            })

    # Sort by Bayesian Weighted Rate as the primary ranking
    upset_leaderboard.sort(key=lambda x: x['Bayesian Weighted Rate (%)'], reverse=True)

    if not upset_leaderboard:
        print(f"\n[!] No teams met the criteria (min_underdog_matches={min_underdog_matches}).")
        return

    # 3. Save to CSV
    csv_name = f"frc_upsets_{year}.csv"
    with open(csv_name, mode='w', newline='') as f:
        fieldnames = ['Team', 'Upset Win Count', 'Underdog Match Count', 'Underdog Match Win Rate (%)', 'Bayesian Weighted Rate (%)', 'Upset Frequency (%)', 'Total Match Count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(upset_leaderboard)

    # 4. Print Results
    print(f"\n--- TOP 10 BRACKET BUSTERS {year} (sorted by Bayesian Weighted Rate) ---")
    print(f"{'Rank':<5} {'Team':<8} | {'Wins':<5} | {'Underdog Win Rate':<20} | {'Bayesian Rate':<16} | {'Upset Frequency'}")
    print("-" * 80)
    for i, row in enumerate(upset_leaderboard[:10]):
        print(f"{i+1:<5} {row['Team']:<8} | {row['Upset Win Count']:<5} | {row['Underdog Match Win Rate (%)']:<19}% | {row['Bayesian Weighted Rate (%)']:<15}% | {row['Upset Frequency (%)']}%")

    print(f"\n  League avg underdog win rate: {round(league_avg_rate * 100, 2)}%")
    print(f"\nSuccess! Full results for {len(upset_leaderboard)} teams saved to {csv_name}")


def find_biggest_upsets(year=2025, top_n=10):
    filename = f"matches_{year}.json"
    with open(filename, 'r') as f:
        matches = json.load(f)

    upset_matches = []

    for m in matches:
        result = m.get('result', {})
        pred = m.get('pred', {})
        winner = result.get('winner')
        red_win_prob = pred.get('red_win_prob')

        if not winner or red_win_prob is None:
            continue

        # If Red won with a low prob, or Blue won when Red had a high prob
        if winner == 'red' and red_win_prob < 0.5:
            underdog_win_probability = red_win_prob
            upset_matches.append((m, underdog_win_probability))
        elif winner == 'blue' and red_win_prob > 0.5:
            underdog_win_probability = 1 - red_win_prob
            upset_matches.append((m, underdog_win_probability))

    # Sort by the lowest win probability
    upset_matches.sort(key=lambda x: x[1])

    print(f"\n--- THE TOP {top_n} BIGGEST UPSETS OF {year} ---")
    print(f"{'Event':<15} | {'Match':<10} | {'Win Probability':<16} | {'Score'}")
    print("-" * 60)

    for match, underdog_win_probability in upset_matches[:top_n]:
        m_name = match.get('match_name', 'N/A')
        event = match.get('event', 'N/A')
        red_score = match.get('result', {}).get('red_score')
        blue_score = match.get('result', {}).get('blue_score')

        print(f"{event:<15} | {m_name:<10} | {round(underdog_win_probability * 100, 2):>13}% | {red_score}-{blue_score}")


if __name__ == "__main__":
    run_analysis(year=2025, min_underdog_matches=2)
    find_biggest_upsets(year=2025)