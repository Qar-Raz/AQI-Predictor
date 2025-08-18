import pandas as pd
import numpy as np
import joblib
import requests
import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


MODEL_FILE = 'models/MAIN MODEL.joblib'
HISTORICAL_DATA_FILE = 'data/karachi_daily_data_5_years.csv'
TIMEZONE = 'Asia/Karachi'
LATITUDE = 24.86
LONGITUDE = 67.01

# Setting up the fastapi app, configs
app = FastAPI(
    title="Pearls AQI Predictor API",
    description="An API to provide today's AQI and a 3-day forecast.",
    version="1.0.0"
)


origins = [
    "http://localhost:3000",
    "localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is the main prediction logic

def get_future_forecast_from_api():
    """Fetches and prepares the forecast for the next 3 days."""
    print("--- Fetching Future Forecast Data ---")
    try:
        FORECAST_DAYS = 4
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

def create_features_for_single_day(forecast_row, history_df):
    """
    Creates ALL features for a single future day using historical context.
    """
    features = {}
    
    # 1. Add the forecast data for the day
    features.update(forecast_row.to_dict())
    
    # 2. Add base features (lags, time)
    for i in range(1, 8):
        features[f'aqi_lag_{i}'] = history_df['aqi'].iloc[-i]
    
    date_to_predict = forecast_row.name
    features['day_of_year'] = date_to_predict.dayofyear
    
    # 3. Add advanced features (rolling, interactions, cyclical)
    window_sizes = [3, 7]
    cols_to_roll = ['aqi', 'pm25', 'carbon_monoxide', 'wind_speed', 'humidity']
    
    temp_df_for_rolling = pd.concat([history_df, pd.DataFrame(forecast_row).T])

    for window in window_sizes:
        for col in cols_to_roll:
            features[f'{col}_rolling_mean_{window}'] = temp_df_for_rolling[col].shift(1).rolling(window=window).mean().iloc[-1]
            features[f'{col}_rolling_std_{window}'] = temp_df_for_rolling[col].shift(1).rolling(window=window).std().iloc[-1]

    features['pm25_x_wind_interaction'] = features['pm25'] / (features['wind_speed'] + 1)
    features['temp_x_humidity_interaction'] = features['temperature'] * features['humidity']
    
    features['month_sin'] = np.sin(2 * np.pi * date_to_predict.month / 12)
    features['month_cos'] = np.cos(2 * np.pi * date_to_predict.month / 12)
    features['day_of_week_sin'] = np.sin(2 * np.pi * date_to_predict.dayofweek / 7)
    features['day_of_week_cos'] = np.cos(2 * np.pi * date_to_predict.dayofweek / 7)
    
    return features

def generate_full_response():
    """
    Loads data and the champion model, generates a 3-day forecast, and returns the result.
    """
    print("\n====== STARTING FULL RESPONSE GENERATION ======")
    try:
        
        model = joblib.load(MODEL_FILE)
        df_historical = pd.read_csv(HISTORICAL_DATA_FILE, parse_dates=['timestamp'])
    except FileNotFoundError as e:
        return {"error": f"Missing required file: {e}. Ensure 'models' and 'data' directories are in the project root."}

    #1: Get Today's Most Recent AQI
    latest_data = df_historical.sort_values('timestamp').iloc[-1]
    today_aqi_data = {
        "date": latest_data['timestamp'].strftime('%Y-%m-%d'),
        "aqi": round(latest_data['aqi'])
    }
    
    #2: Get the Future Forecast Ingredients
    future_data = get_future_forecast_from_api()
    if future_data is None:
        return {"error": "Could not retrieve future weather forecast."}
    
    #3: Generate the 3-day AQI Forecast, is done iteratively (IMP)
    live_history = df_historical.sort_values('timestamp').tail(10).copy()
    MODEL_FEATURES = model.feature_names_in_
    
    predictions = []
    for date_to_predict, forecast_row in future_data.iterrows():
        
        features = create_features_for_single_day(forecast_row, live_history)
        features_df = pd.DataFrame([features])[MODEL_FEATURES]
        predicted_aqi = model.predict(features_df)[0]
        
        predictions.append({
            "date": date_to_predict.strftime('%Y-%m-%d'),
            "predicted_aqi": round(predicted_aqi)
        })
        
        new_row_data = forecast_row.to_dict()
        new_row_data['aqi'] = predicted_aqi
        new_row_df = pd.DataFrame([new_row_data], index=[date_to_predict])
        
        live_history = pd.concat([live_history, new_row_df])
        
    #Assemble the Final Response 
    final_response = {
        "today": today_aqi_data,
        "forecast": predictions
    }
    
    print("====== FULL RESPONSE GENERATION COMPLETE ======")
    return final_response

# API endpoints configured here
@app.get("/api/status")
def get_status():
    """
    Provides the status of the API and the last update time of the model.
    """
    try:
        
        mod_time_unix = os.path.getmtime(MODEL_FILE)
        # Convert it to a human-readable UTC datetime object
        last_updated_dt = datetime.fromtimestamp(mod_time_unix, tz=timezone.utc)

        return {
            "status": "online",
            "model_last_updated_utc": last_updated_dt.isoformat()
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast")
def get_aqi_forecast():
    """
    This endpoint runs the complete prediction pipeline to get today's
    AQI value and a 3-day future forecast.
    """
    print("--- Received request for /forecast ---")
    
    
    response_data = generate_full_response()
    
    
    if "error" in response_data:
        raise HTTPException(status_code=500, detail=response_data["error"])
        
    return response_data

@app.get("/api")
def read_root():
    """
    Root endpoint for the API.
    """
    return {"message": "Welcome to the AQI Predictor API."}