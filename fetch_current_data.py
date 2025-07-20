import requests
import pandas as pd
from datetime import datetime
import pytz  

# --- Configuration ---
LATITUDE = 24.86
LONGITUDE = 67.01
TEMP_STORAGE_CSV = "data/current_day_hourly_data.csv"

def get_the_real_data(latitude, longitude, filename):
    """
    This is the simplest version.
    1. Fetches all data for today.
    2. Merges it.
    3. Filters out the future.
    4. Renames columns ONCE and saves.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"--- Starting fetch for {today_str} ---")

    # --- Step 1: Fetch all data (past + future) ---
    print("Fetching data from APIs...")
    try:
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {"latitude": latitude, "longitude": longitude, "start_date": today_str, "end_date": today_str, "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m", "timezone": "Asia/Karachi"}
        weather_data = requests.get(weather_url, params=weather_params).json()['hourly']
        df_weather = pd.DataFrame(weather_data)

        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {"latitude": latitude, "longitude": longitude, "start_date": today_str, "end_date": today_str, "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,us_aqi", "timezone": "Asia/Karachi"}
        aq_data = requests.get(aq_url, params=aq_params).json()['hourly']
        df_aq = pd.DataFrame(aq_data)
        print(f"-> OK: Fetched {len(df_weather)} total records.")
    except Exception as e:
        print(f"!!! FAILED during API fetch: {e}")
        return

    # --- Step 2: Merge the data ---
    # Both dataframes have a 'time' column, so we merge on that.
    print("Merging data...")
    df_merged = pd.merge(df_weather, df_aq, on='time')

    # --- Step 3: Remove the future data ---
    # This is the most important step.
    print("Filtering out future hours...")
    # Make the 'time' column into a proper, timezone-aware timestamp
    df_merged['time'] = pd.to_datetime(df_merged['time']).dt.tz_localize('Asia/Karachi')
    # Get the current time in the same timezone
    now_in_karachi = datetime.now(pytz.timezone('Asia/Karachi'))
    # Keep only rows from the past
    df_real_data = df_merged[df_merged['time'] <= now_in_karachi].copy()
    print(f"-> OK: Kept {len(df_real_data)} measured records.")

    if df_real_data.empty:
        print("-> No measured hours found for today yet. File not updated.")
        return

    # --- Step 4: Final Cleanup and Save ---
    # We do ONE rename and ONE dropna at the very end.
    print("Cleaning up and saving...")
    
    # This is the modern, safe way to rename and drop missing values.
    df_final = df_real_data.rename({
        'time': 'timestamp',
        'temperature_2m': 'temperature',
        'relative_humidity_2m': 'humidity',
        'wind_speed_10m': 'wind_speed',
        'pm2_5': 'pm25',
        'us_aqi': 'aqi'
    }, axis='columns')
    
    df_final = df_final.dropna()
    
    df_final.to_csv(filename, index=False)
    
    print(f"\n DONE")
    print(f"Saved {len(df_final)} measured hourly records to '{filename}'.")


# --- Main Execution ---
if __name__ == "__main__":
    get_the_real_data(LATITUDE, LONGITUDE, TEMP_STORAGE_CSV)