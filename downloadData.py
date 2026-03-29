import statbotics
import json
import os

sb = statbotics.Statbotics()

def save_year_data(year=2025):
    all_matches = []
    offset = 0
    limit_per_request = 1000
    filename = f"matches_{year}.json"
    
    print(f"Starting download for {year}...")
    
    while True:
        try:
            chunk = sb.get_matches(year=year, limit=limit_per_request, offset=offset)
            if not chunk:
                break
            all_matches.extend(chunk)
            print(f"  > Retrieved {len(all_matches)} matches...")
            offset += limit_per_request
        except Exception:
            break

    with open(filename, 'w') as f:
        json.dump(all_matches, f)
    
    print(f"\nSuccess! Saved {len(all_matches)} matches to {filename}")
    print("You can now run the analysis script without waiting for a download.")

if __name__ == "__main__":
    save_year_data(2025)