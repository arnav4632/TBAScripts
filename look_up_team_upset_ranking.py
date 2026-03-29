import csv

BAYESIAN_CONFIDENCE = 5  # Number of matches needed to fully trust a team's win rate

def lookup_team(team_number, year=2025):
    csv_name = f"frc_upsets_{year}.csv"

    with open(csv_name, newline='') as f:
        rows = list(csv.DictReader(f))

    # Normalize input to match the "frc####" format in the data
    team_key = f"{team_number}"

    total_teams = len(rows)

    # Calculate league-wide average underdog win rate
    total_upset_wins = sum(float(r['Upset Win Count']) for r in rows)
    total_underdog_matches = sum(float(r['Underdog Match Count']) for r in rows)
    league_avg_rate = total_upset_wins / total_underdog_matches

    # Add Bayesian weighted rate to each row
    for r in rows:
        wins = float(r['Upset Win Count'])
        matches = float(r['Underdog Match Count'])
        r['Bayesian Weighted Rate'] = (wins + BAYESIAN_CONFIDENCE * league_avg_rate) / (matches + BAYESIAN_CONFIDENCE)

    # Build separate sorted rankings
    upset_win_count_ranking = sorted(rows, key=lambda x: float(x['Upset Win Count']), reverse=True)
    underdog_win_rate_ranking = sorted(rows, key=lambda x: float(x['Underdog Match Win Rate (%)']), reverse=True)
    bayesian_ranking = sorted(rows, key=lambda x: x['Bayesian Weighted Rate'], reverse=True)

    # Find the team's position in each ranking
    upset_win_count_rank = next((i + 1 for i, r in enumerate(upset_win_count_ranking) if r['Team'] == team_key), None)
    underdog_win_rate_rank = next((i + 1 for i, r in enumerate(underdog_win_rate_ranking) if r['Team'] == team_key), None)
    bayesian_rank = next((i + 1 for i, r in enumerate(bayesian_ranking) if r['Team'] == team_key), None)

    if upset_win_count_rank is None:
        print(f"\n[!] {team_key} not found. They may not have met the minimum underdog match threshold.")
        return

    # Calculate percentiles (higher = better)
    upset_win_count_percentile = round((1 - (upset_win_count_rank - 1) / total_teams) * 100, 1)
    underdog_win_rate_percentile = round((1 - (underdog_win_rate_rank - 1) / total_teams) * 100, 1)
    bayesian_percentile = round((1 - (bayesian_rank - 1) / total_teams) * 100, 1)

    # Find the team's row for stats
    team_row = next(r for r in rows if r['Team'] == team_key)
    bayesian_rate_pct = round(team_row['Bayesian Weighted Rate'] * 100, 1)
    league_avg_pct = round(league_avg_rate * 100, 1)

    print(f"\n--- {team_key.upper()} RANKING ({year}) ---")

    print(f"\n  By Upset Win Count (total underdog matches won):")
    print(f"    Rank:        #{upset_win_count_rank} of {total_teams}")
    print(f"    Percentile:  {upset_win_count_percentile}th")
    print(f"    Value:       {team_row['Upset Win Count']} wins out of {team_row['Underdog Match Count']} underdog matches")

    print(f"\n  By Underdog Match Win Rate (% of underdog matches won):")
    print(f"    Rank:        #{underdog_win_rate_rank} of {total_teams}")
    print(f"    Percentile:  {underdog_win_rate_percentile}th")
    print(f"    Value:       {team_row['Underdog Match Win Rate (%)']}%")

    print(f"\n  By Bayesian Weighted Rate (balances volume and win rate):")
    print(f"    Rank:        #{bayesian_rank} of {total_teams}")
    print(f"    Percentile:  {bayesian_percentile}th")
    print(f"    Value:       {bayesian_rate_pct}%  (league avg: {league_avg_pct}%)")

    print(f"\n  Other Stats:")
    print(f"    Upset Frequency:   {team_row['Upset Frequency (%)']}%")
    print(f"    Total Match Count: {team_row['Total Match Count']}")


if __name__ == "__main__":
    team = input("Enter team number (e.g. 254 or frc254): ").strip()
    year = input("Enter year (default 2025): ").strip()
    year = 2025
    lookup_team(team, year)