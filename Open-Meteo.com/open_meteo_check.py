# This is a simple script to check the current weather and air quality in Karachi.
# It uses the Open-Meteo.com API to get the data.
# It then prints the data to the console in a readable format.
# NOTE: This is not a realtime script, it is just a check.

import requests
import pandas as pd

# To get karachi's data using Open-Meteo.com, you have to use coordinates.
LATITUDE = 24.86
LONGITUDE = 67.01

def get_aqi_category(aqi):
    """
    This just converts the AQI value into a category name. 
    NOTE: AQI is actually returned as a number, this function is just converting it to a category.
    """

    if 0 <= aqi <= 50:
        return "Good"
    elif 51 <= aqi <= 100:
        return "Moderate"
    elif 101 <= aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif 151 <= aqi <= 200:
        return "Unhealthy"
    elif 201 <= aqi <= 300:
        return "Very Unhealthy"
    elif aqi > 300:
        return "Hazardous"
    else:
        return "Unknown"

def get_and_print_current_data(latitude, longitude):
    """
    Gets the latest live weather and air quality data.
    NOTE: We actually have to use 2 seperate API calls.
    1) For Weather data
    2) For AQI data

    Then we combine the data and print it to the console.
    """
    print("Fetching live data for Karachi...")
    
    # 1) Fetch LIVE Weather Data
    try:
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude, "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "Asia/Karachi"
        }
        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()
        current_weather = weather_response.json()['current']
    except Exception as e:
        print(f"!!! ERROR: Could not fetch weather data: {e}")
        return

    # 2) Fetch LIVE AQI Data
    try:
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {
            "latitude": latitude, "longitude": longitude,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,us_aqi",
            "timezone": "Asia/Karachi"
        }
        aq_response = requests.get(aq_url, params=aq_params)
        aq_response.raise_for_status()
        current_aq = aq_response.json()['current']
    except Exception as e:
        print(f"!!! ERROR: Could not fetch air quality data: {e}")
        return

    # 3) Print the Combined Data, in a formatted way.
    aqi_value = current_aq.get('us_aqi')
    aqi_category = get_aqi_category(aqi_value)

    print("\n" + "="*45)
    print("--- Current Conditions in Karachi ---")
    print(f"Timestamp: {pd.to_datetime(current_weather.get('time')).strftime('%Y-%m-%d %I:%M %p')}")
    print("="*45)
    
    print("\n--- Air Quality ---")
    print(f"AQI (US):      {aqi_value} ({aqi_category})")
    print(f"PM2.5:         {current_aq.get('pm2_5')} µg/m³")
    print(f"PM10:          {current_aq.get('pm10')} µg/m³")
    print(f"CO:            {current_aq.get('carbon_monoxide')} µg/m³")
    print(f"NO₂:           {current_aq.get('nitrogen_dioxide')} µg/m³")
    
    print("\n--- Weather ---")
    print(f"Temperature:   {current_weather.get('temperature_2m')}°C")
    print(f"Humidity:      {current_weather.get('relative_humidity_2m')}%")
    print(f"Wind Speed:    {current_weather.get('wind_speed_10m')} km/h")
    print("\n" + "="*45)



if __name__ == "__main__":
    get_and_print_current_data(LATITUDE, LONGITUDE)