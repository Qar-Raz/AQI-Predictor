import pandas as pd
import joblib
import requests
import os
from datetime import date, timedelta

# --- Configuration (using absolute paths for robustness) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(current_dir, '..', 'models', 'aqi_predictor_model.joblib')
HISTORICAL_DATA_FILE = os.path.join(current_dir, '..', 'data', 'karachi_daily_data_5_years.csv')

TIMEZONE = 'Asia/Karachi'
LATITUDE = 24.86
LONGITUDE = 67.01

def get_future_forecast_from_api():
    """Fetches and prepares the forecast for the next 3 days."""
    # This function remains the same as our last working version
    # It fetches 4 days and slices to return the next 3.
    print("--- Fetching Future Forecast Data ---")
    try:
        FORECAST_DAYS = 4
        # ... (API call logic is the same)
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {"latitude": LATITUDE, "longitude": LONGITUDE, "daily": "temperature_2m_mean,relative_humidity_2m_mean,wind_speed_10m_mean", "forecast_days": FORECAST_DAYS, "timezone": TIMEZONE}
        weather_json = requests.get(weather_url, params=weather_params).json()
        
        aq_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        aq_params = {"latitude": LATITUDE, "longitude": LONGITUDE, "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide", "forecast_days": FORECAST_DAYS, "timezone": TIMEZONE}
        aq_json = requests.get(aq_url, params=aq_params).json()

        df_weather_daily = pd.DataFrame(weather_json['daily'])
        df_weather_daily.rename(columns={'time': 'timestamp'}, inplace=True)
        df_weather_daily['timestamp'] = pd.to_datetime(df_weather_daily['timestamp'])
        
        df_aq_hourly = pd.DataFrame(aq_json['hourly'])
        df_aq_hourly.rename(columns={'time': 'timestamp'}, inplace=True)
        df_aq_hourly['timestamp'] = pd.to_datetime(df_aq_hourly['timestamp'])
        
        df_aq_hourly.set_index('timestamp', inplace=True)
        pollutant_columns = ['pm10', 'pm2_5', 'carbon_monoxide', 'nitrogen_dioxide']
        df_aq_daily = df_aq_hourly[pollutant_columns].resample('D').mean()
        
        forecast_df = pd.merge(df_weather_daily.set_index('timestamp'), df_aq_daily, left_index=True, right_index=True)
        forecast_df.rename(columns={'temperature_2m_mean': 'temperature', 'relative_humidity_2m_mean': 'humidity', 'wind_speed_10m_mean': 'wind_speed', 'pm2_5': 'pm25'}, inplace=True)
        
        future_days_only = forecast_df.iloc[1:]
        print(f"-> OK: Future forecast data fetched for the next {len(future_days_only)} days.")
        return future_days_only
    except Exception as e:
        print(f"!!! FATAL: An error occurred during API fetch: {e}")
        return None

def generate_full_response():
    """
    This is the new master function. It loads all data and models,
    gets today's AQI, generates the 3-day forecast, and returns a single object.
    """
    print("\n====== STARTING FULL RESPONSE GENERATION ======")
    try:
        model = joblib.load(MODEL_FILE)
        df_historical_pool = pd.read_csv(HISTORICAL_DATA_FILE, parse_dates=['timestamp'])
    except FileNotFoundError as e:
        error_msg = f"Missing required file: {e}"
        print(f"!!! FATAL ERROR: {error_msg}")
        return {"error": error_msg}

    # --- Step 1: Get Today's Most Recent AQI ---
    latest_data = df_historical_pool.sort_values('timestamp').iloc[-1]
    today_aqi_data = {
        "date": latest_data['timestamp'].strftime('%Y-%m-%d'),
        "aqi": round(latest_data['aqi'])
    }
    
    # --- Step 2: Get the Future Forecast Ingredients ---
    future_data = get_future_forecast_from_api()
    if future_data is None:
        return {"error": "Could not retrieve future weather forecast."}
    
    # --- Step 3: Generate the 3-day AQI Forecast ---
    prediction_seed_data = df_historical_pool.sort_values('timestamp').tail(7).copy()
    
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
        
    # --- Step 4: Assemble the Final Response ---
    final_response = {
        "today": today_aqi_data,
        "forecast": predictions
    }
    
    print("====== FULL RESPONSE GENERATION COMPLETE ======")
    return final_response

# Main block for direct testing
if __name__ == "__main__":
    result = generate_full_response()
    print("\n--- ✅ Final Result ---")
    print(result)