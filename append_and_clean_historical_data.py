import pandas as pd
import sys

# --- Configuration ---
MAIN_HISTORICAL_FILE = "data/karachi_daily_data_5_years.csv"
NEW_DAILY_DATA_FILE = "data/last_7_days_daily_data.csv"
TIMEZONE = 'Asia/Karachi' # Define timezone as a constant for consistency

def append_and_clean_historical_data(main_file, new_data_file):
    """
    Efficiently appends new daily data to the main historical dataset.
    
    This function is idempotent: it combines data, removes any overlaps by
    keeping the newest data, and saves a clean, sorted historical file.
    It robustly handles both timezone-aware and timezone-naive data.
    """
    print("--- Starting historical data update process ---")

    # --- Step 1: Load the main historical dataset ---
    try:
        df_main = pd.read_csv(main_file, parse_dates=['timestamp'])
        
        # === FIX 1: LOCALIZE THE MAIN DATAFRAME'S TIMESTAMP ===
        # If the timestamp column is naive, assign the correct timezone.
        # If it's already aware, this will correctly convert it.
        if df_main['timestamp'].dt.tz is None:
            df_main['timestamp'] = df_main['timestamp'].dt.tz_localize(TIMEZONE)
        else:
            df_main['timestamp'] = df_main['timestamp'].dt.tz_convert(TIMEZONE)
            
        print(f"Loaded and standardized {len(df_main)} records from the main historical file.")
    except FileNotFoundError:
        print(f"!!! ERROR: New daily data file '{new_data_file}' not found. Aborting.")
        sys.exit(1)

    # --- Step 2: Load the new daily data ---
    try:
        df_new = pd.read_csv(new_data_file, parse_dates=['timestamp'])
        
        # === FIX 2: LOCALIZE THE NEW DATAFRAME'S TIMESTAMP (just in case) ===
        # This ensures the new data is also tz-aware before concatenation.
        if df_new['timestamp'].dt.tz is None:
            df_new['timestamp'] = df_new['timestamp'].dt.tz_localize(TIMEZONE)
        else:
            df_new['timestamp'] = df_new['timestamp'].dt.tz_convert(TIMEZONE)

        print(f"Loaded and standardized {len(df_new)} new daily records to be merged.")
    except FileNotFoundError:
        print(f"!!! ERROR: New daily data file '{new_data_file}' not found. Aborting.")
        return

    # --- Step 3: Combine and De-duplicate (This will now work) ---
    print("Combining datasets and removing duplicates...")
    
    # Now that both dataframes have tz-aware timestamps, this is safe.
    df_combined = pd.concat([df_main, df_new], ignore_index=True)
    
    df_final = df_combined.sort_values('timestamp').drop_duplicates(subset=['timestamp'], keep='last')
    
    print(f"-> Combined records: {len(df_combined)}")
    print(f"-> Records after de-duplication: {len(df_final)}")
    
    # --- Step 4: Save the updated historical dataset ---
    df_final.to_csv(main_file, index=False)
    
    print(f"\n✅ --- SUCCESS --- ✅")
    print(f"Main historical dataset '{main_file}' has been updated.")
    print(f"It now contains {len(df_final)} clean, unique daily records.")


# --- Run the script ---
if __name__ == "__main__":
    append_and_clean_historical_data(MAIN_HISTORICAL_FILE, NEW_DAILY_DATA_FILE)