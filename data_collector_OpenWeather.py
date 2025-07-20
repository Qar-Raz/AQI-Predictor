import requests
import pandas as pd
from datetime import datetime
import os

# this works but the data is only for the current day
# Also the aqi is in the range of 1-5, so not regression


# Replace with your actual API key
API_KEY = "b4522af69d41155dc1c3ead5ba78497e"

# Karachi coordinates
LAT = 24.8607
LON = 67.0011

def fetch_aqi_openweather():
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        main = data['list'][0]['main']
        components = data['list'][0]['components']

        aqi_info = {
            "timestamp": datetime.now().isoformat(),
            "aqi": main['aqi'],  # Scale: 1=Good, 5=Very Poor
            "pm2_5": components['pm2_5'],
            "pm10": components['pm10'],
            "co": components['co'],
            "no2": components['no2'],
            "so2": components['so2'],
            "o3": components['o3']
        }

        return pd.DataFrame([aqi_info])

    else:
        print("Failed to fetch AQI data:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    df = fetch_aqi_openweather()
    if df is not None:
        print(df)

        # Make sure 'data/' folder exists
        os.makedirs("data", exist_ok=True)

        csv_path = "data/openweather_karachi_aqi.csv"

        # Save to CSV in 'data' folder
        df.to_csv(csv_path, mode='a', header=not os.path.exists(csv_path), index=False)