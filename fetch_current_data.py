import requests
import pandas as pd
from datetime import datetime, date, timedelta
import pytz

# --- Configuration ---
LATITUDE = 24.86
LONGITUDE = 67.01
# This file will store a COMPLETE rolling 7-day history of hourly data
HISTORICAL_CSV = "data/last_7_days_hourly_data.csv"

def get_complete_past_week_hourly_data(latitude, longitude, filename):
    """
    Fetches a complete, seamless 7-day history of hourly data by combining
    the historical archive with the most recent real-time measurements.
    
    This version is simplified and more robust.
    """
    print("--- Starting full historical data assembly ---")

    # --- Step 1: Fetch HISTORICAL data (Archive API for reliability) ---
    # We fetch the bulk of the data from the reliable archive.
    hist_end_date = date.today()
    hist_start_date = date.today() - timedelta(days=8) # Go back 8 days to ensure we have a full 7
    
    print(f"Fetching historical archive from {hist_start_date} to {hist_end_date}...")
    try:
        # Get Weather History
        weather_url = "https://archive-api.open-meteo.com/v1/archive"
        weather_params = {"latitude": latitude, "longitude": longitude, "start_date": hist_start_date.strftime("%Y-%m-%d"), "end_date": hist_end_date.strftime("%Y-%m-%d"), "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m", "timezone": "Asia/Karachi"}
        df_weather_hist = pd.DataFrame(requests.get(weather_url, params=weather_params).json()['hourly'])

        # Get Air Quality History
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {"latitude": latitude, "longitude": longitude, "start_date": hist_start_date.strftime("%Y-%m-%d"), "end_date": hist_end_date.strftime("%Y-%m-%d"), "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,us_aqi", "timezone": "Asia/Karachi"}
        df_aq_hist = pd.DataFrame(requests.get(aq_url, params=aq_params).json()['hourly'])
        
        # Merge, process, and clean the historical data
        df_historical = pd.merge(df_weather_hist, df_aq_hist, on='time')
        df_historical['time'] = pd.to_datetime(df_historical['time'])
        print(f"-> OK: Fetched {len(df_historical)} records from archive.")
    except Exception as e:
        print(f"!!! WARNING: Could not fetch historical data. Reason: {e}")
        df_historical = pd.DataFrame() # Create an empty dataframe to allow the script to continue


    # --- Step 2: Fetch RECENT data (Forecast API for up-to-the-minute values) ---
    # This gets today's measured data, filling the gap from the archive's lag.
    today_str = date.today().strftime("%Y-%m-%d")
    print(f"Fetching recent measured data for {today_str}...")
    try:
        # Get Recent Weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {"latitude": latitude, "longitude": longitude, "start_date": today_str, "end_date": today_str, "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m", "timezone": "Asia/Karachi"}
        df_weather_recent = pd.DataFrame(requests.get(weather_url, params=weather_params).json()['hourly'])

        # Get Recent Air Quality
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {"latitude": latitude, "longitude": longitude, "start_date": today_str, "end_date": today_str, "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,us_aqi", "timezone": "Asia/Karachi"}
        df_aq_recent = pd.DataFrame(requests.get(aq_url, params=aq_params).json()['hourly'])

        # Merge and process the recent data
        df_recent = pd.merge(df_weather_recent, df_aq_recent, on='time')
        df_recent['time'] = pd.to_datetime(df_recent['time'])
        print(f"-> OK: Fetched {len(df_recent)} recent records.")
    except Exception as e:
        print(f"!!! WARNING: Could not fetch recent data. Reason: {e}")
        df_recent = pd.DataFrame()


    # --- Step 3: Combine, De-duplicate, and Filter ---
    print("Combining and cleaning final dataset...")
    # Combine the two data sources
    df_combined = pd.concat([df_historical, df_recent])

    # Important: Drop duplicates on the 'time' column.
    # 'keep=last' ensures the more up-to-date data from the Forecast API is used for any overlap.
    df_combined = df_combined.drop_duplicates(subset='time', keep='last').sort_values(by='time')

    # Now that we have a clean, combined dataframe, filter out future hours
    df_combined['time'] = df_combined['time'].dt.tz_localize('Asia/Karachi', ambiguous='infer')
    now_in_karachi = datetime.now(pytz.timezone('Asia/Karachi'))
    df_measured = df_combined[df_combined['time'] <= now_in_karachi].copy()

    # Finally, keep only the last 7 days of data
    seven_days_ago = now_in_karachi - timedelta(days=7)
    df_final_week = df_measured[df_measured['time'] >= seven_days_ago]
    
    # --- Step 4: Final Rename and Save ---
    df_final = df_final_week.rename({
        'time': 'timestamp',
        'temperature_2m': 'temperature',
        'relative_humidity_2m': 'humidity',
        'wind_speed_10m': 'wind_speed',
        'pm2_5': 'pm25',
        'us_aqi': 'aqi'
    }, axis='columns').dropna()

    df_final.to_csv(filename, index=False)
    
    print(f"\n✅ DONE ✅")
    print(f"Saved {len(df_final)} hourly records to '{filename}', covering a complete and up-to-date 7-day period.")


# --- Main Execution ---
if __name__ == "__main__":
    get_complete_past_week_hourly_data(LATITUDE, LONGITUDE, HISTORICAL_CSV)