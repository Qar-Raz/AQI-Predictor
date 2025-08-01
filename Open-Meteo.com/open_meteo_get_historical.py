import requests
import pandas as pd
from datetime import date, timedelta

# --- Configuration ---
LATITUDE = 24.86
LONGITUDE = 67.01
# Let's get the last year of data. You can adjust this.
START_DATE = date.today() - timedelta(days=365)
END_DATE = date.today() - timedelta(days=1)
CSV_FILE = "data/karachi_hourly_data.csv"

def fetch_and_save_hourly_data(latitude, longitude, start_date, end_date, filename):
    """
    This function fetches raw hourly data for both air quality and weather,
    merges them, and saves the result to a CSV file.
    """
    print("--- Starting Data Fetch ---")
    
    # 1. --- Fetch HOURLY Air Quality Data ---
    # This uses the standard hourly parameters which are very reliable.
    print("Step 1: Fetching Hourly Air Quality Data...")
    aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    # NOTE: Using the basic, reliable hourly variables.
    aq_params = {
        "latitude": latitude, "longitude": longitude,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,us_aqi",
        "timezone": "Asia/Karachi"
    }
    
    try:
        aq_response = requests.get(aq_url, params=aq_params)
        aq_response.raise_for_status()
        aq_data = aq_response.json()['hourly']
        df_aq = pd.DataFrame(aq_data)
        df_aq.rename(columns={'time': 'timestamp'}, inplace=True)
        print("-> OK: Air Quality data fetched.")
    except Exception as e:
        print(f"!!! FATAL ERROR fetching Air Quality data: {e}")
        # Print the response text to see the error message from the server
        if 'aq_response' in locals():
            print("API Server Response:", aq_response.text)
        return False

    # 2. --- Fetch HOURLY Weather Data ---
    # This uses the reliable archive API for historical weather.
    print("\nStep 2: Fetching Hourly Weather Data...")
    weather_url = "https://archive-api.open-meteo.com/v1/archive"
    weather_params = {
        "latitude": latitude, "longitude": longitude,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "Asia/Karachi"
    }

    try:
        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()['hourly']
        df_weather = pd.DataFrame(weather_data)
        df_weather.rename(columns={'time': 'timestamp'}, inplace=True)
        print("-> OK: Weather data fetched.")
    except Exception as e:
        print(f"!!! FATAL ERROR fetching Weather data: {e}")
        if 'weather_response' in locals():
            print("API Server Response:", weather_response.text)
        return False

    # 3. --- Merge and Save ---
    print("\nStep 3: Merging data...")
    # Convert timestamp columns to datetime objects to ensure a perfect merge
    df_aq['timestamp'] = pd.to_datetime(df_aq['timestamp'])
    df_weather['timestamp'] = pd.to_datetime(df_weather['timestamp'])

    # Merge the two DataFrames on the common 'timestamp' column
    df_merged = pd.merge(df_aq, df_weather, on='timestamp')
    
    # Clean up column names
    df_merged.rename(columns={
        'pm2_5': 'pm25',
        'us_aqi': 'aqi',
        'temperature_2m': 'temperature',
        'relative_humidity_2m': 'humidity',
        'wind_speed_10m': 'wind_speed'
    }, inplace=True)
    
    # Save the final, merged hourly data
    df_merged.to_csv(filename, index=False)
    
    print(f"\n✅ --- SUCCESS --- ✅")
    print(f"All hourly data has been saved to '{filename}'")
    print(f"The file contains {len(df_merged)} hourly records.")
    return True


if __name__ == "__main__":
    fetch_and_save_hourly_data(LATITUDE, LONGITUDE, START_DATE, END_DATE, CSV_FILE)