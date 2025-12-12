#!/usr/bin/env python3
"""
Script to combine all CSV files from the schedules folder into a single CSV.
"""

import pandas as pd
import os
from pathlib import Path

def combine_schedules():
    """Combine all CSV files in the schedules folder into a single CSV."""
    
    schedules_dir = Path("schedules")
    output_file = "combined_schedules.csv"
    
    # Get all CSV files in the schedules directory
    csv_files = list(schedules_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in the schedules folder.")
        return
    
    print(f"Found {len(csv_files)} CSV files to combine.")
    
    # List to store all dataframes
    all_dataframes = []
    
    # Read each CSV file and add a source column
    for csv_file in csv_files:
        try:
            # Try reading with standard settings first
            df = pd.read_csv(csv_file, quotechar='"')
            # Add source column with the filename (without extension)
            df['Source'] = csv_file.stem
            all_dataframes.append(df)
            print(f"  - Loaded {csv_file.name}: {len(df)} rows")
        except Exception as e:
            # If that fails, try with Python engine which is more lenient
            try:
                df = pd.read_csv(csv_file, quotechar='"', engine='python', on_bad_lines='skip')
                # Ensure we have the right number of columns
                if len(df.columns) >= 5:
                    # Take only the first 5 columns if there are more
                    df = df.iloc[:, :5]
                    df.columns = ['Date', 'Time', 'Artist(s)', 'Instruments/Details', 'Venue']
                    df['Source'] = csv_file.stem
                    all_dataframes.append(df)
                    print(f"  - Loaded {csv_file.name}: {len(df)} rows (with error handling)")
                else:
                    print(f"  - Error reading {csv_file.name}: Not enough columns")
            except Exception as e2:
                # Last resort: try with even more lenient settings
                try:
                    df = pd.read_csv(csv_file, engine='python', sep=',', quotechar='"', 
                                    on_bad_lines='skip', skipinitialspace=True)
                    if len(df.columns) >= 5:
                        df = df.iloc[:, :5]
                        df.columns = ['Date', 'Time', 'Artist(s)', 'Instruments/Details', 'Venue']
                        df['Source'] = csv_file.stem
                        all_dataframes.append(df)
                        print(f"  - Loaded {csv_file.name}: {len(df)} rows (with lenient parsing)")
                    else:
                        print(f"  - Error reading {csv_file.name}: Not enough columns after parsing")
                except Exception as e3:
                    print(f"  - Error reading {csv_file.name}: {e3}")
    
    if not all_dataframes:
        print("No dataframes were successfully loaded.")
        return
    
    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Reorder columns to put Source at the end (or beginning, your choice)
    columns = ['Date', 'Time', 'Artist(s)', 'Instruments/Details', 'Venue', 'Source']
    combined_df = combined_df[columns]
    
    # Write to output file
    combined_df.to_csv(output_file, index=False)
    
    print(f"\nSuccessfully combined {len(all_dataframes)} files into {output_file}")
    print(f"Total rows: {len(combined_df)}")
    print(f"Total columns: {len(combined_df.columns)}")
    
    return combined_df

if __name__ == "__main__":
    combine_schedules()

