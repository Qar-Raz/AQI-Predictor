import pandas as pd
import joblib
import requests
import os
from datetime import date, timedelta

# --- Configuration ---
# Use os.path.join for platform independence
MODEL_FILE = os.path.join('models', 'aqi_predictor_model.joblib')
HISTORICAL_DATA_FILE = os.path.join('data', 'karachi_daily_data_5_years.csv')
TIMEZONE = 'Asia/Karachi'
LATITUDE = 24.86
LONGITUDE = 67.01

def get_future_forecast_from_api():
    """
    Fetches the 3-day forecast. It gets daily weather but fetches HOURLY 
    air quality data and aggregates it to daily to match the training data format.
    """
    print("--- Fetching 3-Day Future Forecast Data ---")
    try:
        # 1. Fetch Daily Weather Forecast (This part is fine)
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {"latitude": LATITUDE, "longitude": LONGITUDE, "daily": "temperature_2m_mean,relative_humidity_2m_mean,wind_speed_10m_mean", "forecast_days": 3, "timezone": TIMEZONE}
        weather_response = requests.get(weather_url, params=weather_params)
        weather_response.raise_for_status()
        weather_json = weather_response.json()
        
        if 'daily' not in weather_json:
            print(f"!!! API ERROR (Weather): 'daily' key not in response. Response was: {weather_json}")
            return None
        
        df_weather_daily = pd.DataFrame(weather_json['daily'])
        df_weather_daily.rename(columns={'time': 'timestamp'}, inplace=True)
        df_weather_daily['timestamp'] = pd.to_datetime(df_weather_daily['timestamp'])

        # 2. === FIX: Fetch HOURLY Air Quality Forecast ===
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {"latitude": LATITUDE, "longitude": LONGITUDE, "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide", "forecast_days": 3, "timezone": TIMEZONE}
        aq_response = requests.get(aq_url, params=aq_params)
        aq_response.raise_for_status()
        aq_json = aq_response.json()

        if 'hourly' not in aq_json:
            print(f"!!! API ERROR (Air Quality): 'hourly' key not in response. Response was: {aq_json}")
            return None
            
        df_aq_hourly = pd.DataFrame(aq_json['hourly'])
        df_aq_hourly.rename(columns={'time': 'timestamp'}, inplace=True)
        df_aq_hourly['timestamp'] = pd.to_datetime(df_aq_hourly['timestamp'])

        # 3. === FIX: Aggregate the hourly AQ data to daily means ===
        df_aq_hourly.set_index('timestamp', inplace=True)
        # We only need the pollutants, not AQI which isn't in the forecast
        pollutant_columns = ['pm10', 'pm2_5', 'carbon_monoxide', 'nitrogen_dioxide']
        df_aq_daily = df_aq_hourly[pollutant_columns].resample('D').mean()
        
        # 4. Combine the daily weather and daily aggregated AQ data
        # We merge on the index (the date)
        forecast_df = pd.merge(df_weather_daily.set_index('timestamp'), df_aq_daily, left_index=True, right_index=True)
        
        # Rename columns to match model's expected feature names
        forecast_df.rename(columns={
            'temperature_2m_mean': 'temperature',
            'relative_humidity_2m_mean': 'humidity',
            'wind_speed_10m_mean': 'wind_speed',
            'pm2_5': 'pm25'
        }, inplace=True)
        
        print("-> OK: Future forecast data fetched and aggregated.")
        return forecast_df
        
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! FATAL: HTTP error occurred: {http_err}")
        return None
    except Exception as e:
        print(f"!!! FATAL: An unexpected error occurred during API fetch: {e}")
        return None

def generate_forecast_from_files():
    """
    The main prediction function. It loads all necessary files,
    fetches a future forecast, and generates the 3-day prediction.
    
    This is the function your FastAPI endpoint will call.
    """
    print("\n====== STARTING PREDICTION PIPELINE ======")
    try:
        # Step 1: Load the pre-trained model
        model = joblib.load(MODEL_FILE)
        print(f"-> Model loaded from '{MODEL_FILE}'.")
        
        # Step 2: Load the most recent historical data
        df_historical_pool = pd.read_csv(HISTORICAL_DATA_FILE, parse_dates=['timestamp'])
        print(f"-> Historical data loaded from '{HISTORICAL_DATA_FILE}'.")
        
    except FileNotFoundError as e:
        print(f"!!! FATAL ERROR: Cannot find required file for prediction: {e}")
        # In a FastAPI context, this would return an HTTP error
        return {"error": f"Missing required file: {e}"}

    # Step 3: Fetch the future weather/pollutant data from the API
    future_data = get_future_forecast_from_api()
    if future_data is None:
        return {"error": "Could not retrieve future weather forecast."}
    
    # Step 4: Prepare the "seed" data (last 7 days) for prediction
    prediction_seed_data = df_historical_pool.sort_values('timestamp').tail(7).copy()
    
    # Step 5: Perform the sequential (autoregressive) forecast
    predictions = []
    live_history = prediction_seed_data.copy()
    MODEL_FEATURES = model.feature_names_in_

    for date_to_predict, forecast_row in future_data.iterrows():
        features = {}
        features.update(forecast_row.to_dict())
        for i in range(1, 8):
            features[f'aqi_lag_{i}'] = live_history['aqi'].iloc[-i]
        
        features['month'] = date_to_predict.month
        features['day_of_year'] = date_to_predict.dayofyear
        features['day_of_week'] = date_to_predict.dayofweek
        
        features_df = pd.DataFrame([features])[MODEL_FEATURES]
        predicted_aqi = model.predict(features_df)[0]
        
        predictions.append({
            "date": date_to_predict.strftime('%Y-%m-%d'),
            "predicted_aqi": round(predicted_aqi)
        })
        
        new_row = pd.DataFrame({'aqi': [predicted_aqi]}, index=[pd.to_datetime(date_to_predict)])
        live_history = pd.concat([live_history, new_row])
        
    print("====== PREDICTION PIPELINE COMPLETE ======")
    return {"forecast": predictions}


# This allows you to test the prediction logic directly by running "python prediction.py"
if __name__ == "__main__":
    forecast_result = generate_forecast_from_files()
    
    print("\n--- ✅ Forecast Result ---")
    if "error" in forecast_result:
        print(f"An error occurred: {forecast_result['error']}")
    else:
        for day_forecast in forecast_result.get("forecast", []):
            print(f"Date: {day_forecast['date']}, Predicted AQI: {day_forecast['predicted_aqi']}")