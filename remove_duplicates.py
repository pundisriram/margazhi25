#!/usr/bin/env python3
"""
Remove duplicate entries from combined_schedules.csv.
Duplicates are identified by Date, Time, Artist(s), and Venue.
"""

import pandas as pd
from pathlib import Path

def remove_duplicates(input_file="combined_schedules.csv", output_file="combined_schedules.csv"):
    """Remove duplicate entries based on Date, Time, Artist(s), and Venue."""
    
    # Load the data
    df = pd.read_csv(input_file)
    
    print(f"Original rows: {len(df)}")
    
    # Identify duplicates based on key columns
    # Use Date, Time, and Artist(s) - venue can vary slightly
    key_cols = ['Date', 'Time', 'Artist(s)']
    
    # Normalize venue names for better duplicate detection (remove common suffixes)
    df['VenueNormalized'] = df['Venue'].astype(str).str.replace(
        r',\s*The Music Academy.*$', '', regex=True, case=False
    ).str.strip()
    
    # Check for duplicates with normalized venues
    df['DuplicateKey'] = df['Date'].astype(str) + '|' + df['Time'].astype(str) + '|' + df['Artist(s)'].astype(str) + '|' + df['VenueNormalized'].astype(str)
    
    # Find duplicates
    duplicates = df[df.duplicated(subset=['DuplicateKey'], keep=False)]
    
    if len(duplicates) > 0:
        print(f"\nFound {len(duplicates)} potential duplicate rows (with venue normalization)")
        # Group by the key and show which to remove
        for key, group in duplicates.groupby('DuplicateKey'):
            if len(group) > 1:
                print(f"\nDuplicate group ({len(group)} entries):")
                print(group[['Date', 'Time', 'Artist(s)', 'Venue', 'Source']].to_string())
                # Keep the one with the most complete venue name
                group['VenueLength'] = group['Venue'].astype(str).str.len()
                to_remove = group[group['VenueLength'] != group['VenueLength'].max()].index
                df = df.drop(to_remove)
                print(f"Removed {len(to_remove)} duplicate(s)")
    
    # Also do standard duplicate removal
    df_deduped = df.drop_duplicates(subset=key_cols, keep='first')
    
    # Remove the helper columns
    df_deduped = df_deduped.drop(columns=['VenueNormalized', 'DuplicateKey'], errors='ignore')
    
    print(f"After removing duplicates: {len(df_deduped)}")
    print(f"Removed {len(df) - len(df_deduped)} duplicate rows")
    
    # Show which sources were affected
    duplicates = df[df.duplicated(subset=key_cols, keep=False)]
    if len(duplicates) > 0:
        print(f"\nSources involved in duplicates:")
        print(duplicates['Source'].value_counts())
    
    # Save the deduplicated data
    df_deduped.to_csv(output_file, index=False)
    print(f"\nSaved deduplicated data to {output_file}")
    
    return df_deduped

if __name__ == "__main__":
    # Create backup first
    import shutil
    backup_file = "combined_schedules_backup.csv"
    if Path("combined_schedules.csv").exists():
        shutil.copy("combined_schedules.csv", backup_file)
        print(f"Created backup: {backup_file}")
    
    # Remove duplicates
    remove_duplicates()

