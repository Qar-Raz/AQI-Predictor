# This script is used to convert the hourly data to daily data.
# It is used to get the daily average and maximum AQI.
# It is used to get the daily average and maximum temperature, humidity, and wind speed.
# NOTE: This this is called after the hourly data is fetched, by running the open_meteo_get_historical.py script.
# We have to do this as Open-Meteo.com only gives us hourly data, so I had to code this to aggregate the hourly data to daily data.

import pandas as pd
import sys

# NEVER USE \ IN THE FILE PATHS. IT WILL WORK ON WINDOWS BUT NOT ON LINUX. SO B/C OF THIS THE PIPELINE FAILS
# SMOLL CHANGE CAUSED BIG FAILURE
# --- Configuration ---
HOURLY_DATA_FILE = "data/last_7_days_hourly_data.csv"
DAILY_DATA_FILE = "data/last_7_days_daily_data.csv"

# --- Main Processing ---
def process_hourly_to_daily_correctly(input_file, output_file):
    """
    Loads hourly data and correctly aggregates it to daily data.
    - Averages pollutants and weather variables.
    - Takes the maximum value for the final AQI score.
    """
    try:
        print(f"Loading hourly data from '{input_file}'...")
        # Load the data, ensuring the 'timestamp' column is parsed as a date object.
        df_hourly = pd.read_csv(input_file, parse_dates=['timestamp'])
        df_hourly.set_index('timestamp', inplace=True)
        print("-> Hourly data loaded successfully.")
    except FileNotFoundError:
        print(f"!!! ERROR: The input file '{input_file}' was not found.")
        print("Please run the previous script to generate this file first.")
        sys.exit(1)

    print("\nProcessing daily aggregations...")

    # 1. Calculate the daily MEAN for pollutants and weather data
    # This is the correct method for these linear values.
    daily_means = df_hourly.drop(columns=['aqi']).resample('D').mean()
    print("-> Calculated daily means for pollutants and weather.")

    # 2. Calculate the daily MAXIMUM for the AQI column
    # This is a more meaningful representation than a simple average of the index.
    daily_max_aqi = df_hourly['aqi'].resample('D').max()
    print("-> Calculated daily maximum for AQI.")

    # 3. Combine the results
    # We now have the mean of the raw data and the max of the index.
    df_daily_final = pd.concat([daily_means, daily_max_aqi], axis=1)

    # 4. Clean up
    # Remove any days that might have no data (e.g., if there was a gap in the source)
    df_daily_final.dropna(inplace=True)

    # Save the correctly processed daily data to a new CSV
    df_daily_final.to_csv(output_file)

    print(f"\n✅ --- SUCCESS --- ✅")
    print(f"Correctly processed daily data has been saved to '{output_file}'")
    print(f"The file contains {len(df_daily_final)} daily records.")
    
    # Display the first few rows of the final, correct data
    print("\n--- Sample of Correctly Processed Daily Data ---")
    print(df_daily_final.head())


# --- Run the script ---
if __name__ == "__main__":
    process_hourly_to_daily_correctly(HOURLY_DATA_FILE, DAILY_DATA_FILE)