# =============================================================================
# AQI PREDICTION - CHAMPION MODEL TRAINING SCRIPT
# =============================================================================
#
# Description:
# This script automates the process of training the champion AQI prediction model.
# It performs the following steps:
#   1. Loads the latest daily data.
#   2. Preprocesses the data (handles timestamps).
#   3. Performs two stages of feature engineering (lags, rolling stats, interactions, etc.).
#   4. Defines the top 3 optimized base models (RandomForest, CatBoost, XGBoost).
#   5. Trains a Weighted Averaging Ensemble model on the entire dataset.
#   6. Saves the final, trained model object to a joblib file for use in prediction.


import pandas as pd
import numpy as np
import joblib
import os
import time

# --- Model Imports ---
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
import xgboost as xgb
import catboost as cb

# --- CONFIGURATION ---
# Define file paths here to make them easy to change.
DATA_FILE_PATH = 'data/karachi_daily_data_5_years.csv'
MODEL_OUTPUT_DIR = 'models'
MODEL_FILENAME = 'MAIN MODEL.joblib'

# --- DATA PROCESSING FUNCTIONS ---

def load_and_preprocess_data(file_path):
    """Loads and cleans the raw dataset."""
    print(f"1/4: Loading and preprocessing data from '{file_path}'...")
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    print("     ...Data loaded and preprocessed.")
    return df

def create_base_features(df, lags=7):
    """Creates the initial lag and time-based features."""
    print("2/4: Creating base features (lags and time)...")
    df_featured = df.copy()
    
    # Lag Features for AQI
    for i in range(1, lags + 1):
        df_featured[f'aqi_lag_{i}'] = df_featured['aqi'].shift(i)

    # Time-Based Features
    df_featured['month'] = df_featured.index.month
    df_featured['day_of_year'] = df_featured.index.dayofyear
    df_featured['day_of_week'] = df_featured.index.dayofweek
    
    print("     ...Base features created.")
    return df_featured

def create_advanced_features(df):
    """Creates advanced rolling stats, interactions, and cyclical features."""
    print("3/4: Creating advanced features (rolling stats, interactions, cyclical)...")
    df_advanced = df.copy()

    # Rolling Window Features
    window_sizes = [3, 7]
    cols_to_roll = ['aqi', 'pm25', 'carbon_monoxide', 'wind_speed', 'humidity']
    for window in window_sizes:
        for col in cols_to_roll:
            df_advanced[f'{col}_rolling_mean_{window}'] = df_advanced[col].shift(1).rolling(window=window).mean()
            df_advanced[f'{col}_rolling_std_{window}'] = df_advanced[col].shift(1).rolling(window=window).std()

    # Interaction Features
    df_advanced['pm25_x_wind_interaction'] = df_advanced['pm25'] / (df_advanced['wind_speed'] + 1)
    df_advanced['temp_x_humidity_interaction'] = df_advanced['temperature'] * df_advanced['humidity']

    # Cyclical Features
    df_advanced['month_sin'] = np.sin(2 * np.pi * df_advanced['month'] / 12)
    df_advanced['month_cos'] = np.cos(2 * np.pi * df_advanced['month'] / 12)
    df_advanced['day_of_week_sin'] = np.sin(2 * np.pi * df_advanced['day_of_week'] / 7)
    df_advanced['day_of_week_cos'] = np.cos(2 * np.pi * df_advanced['day_of_week'] / 7)
    df_advanced.drop(['month', 'day_of_week'], axis=1, inplace=True)
    
    # Drop NaNs created by the feature engineering process
    df_advanced.dropna(inplace=True)
    print("     ...Advanced features created.")
    return df_advanced

def train_champion_model(df, output_path):
    """Trains the final weighted ensemble model and saves it to a file."""
    print(f"4/4: Training the champion model...")
    
    # --- a. Define the top-performing base models with their best parameters ---
    rf_model = RandomForestRegressor(
        n_estimators=200, max_depth=20, max_features='sqrt',
        min_samples_split=2, min_samples_leaf=1, random_state=42, n_jobs=-1
    )
    catboost_model = cb.CatBoostRegressor(
        iterations=300, learning_rate=0.05, depth=4,
        l2_leaf_reg=3, random_state=42, verbose=0
    )
    xgboost_model = xgb.XGBRegressor(
        n_estimators=100, max_depth=3, learning_rate=0.1,
        subsample=0.7, colsample_bytree=0.8, random_state=42, n_jobs=-1
    )
    
    # --- b. Define the Weighted Averaging Ensemble (VotingRegressor) ---
    # The weights correspond to the confidence in each model (40%, 40%, 20%)
    estimators = [
        ('Optimized RandomForest', rf_model),
        ('Optimized CatBoost', catboost_model),
        ('Optimized XGBoost', xgboost_model)
    ]
    weights = [0.4, 0.4, 0.2]
    
    ensemble_model = VotingRegressor(estimators=estimators, weights=weights)

    # --- c. Prepare final data and train the model ---
    X_full = df.drop('aqi', axis=1)
    y_full = df['aqi']
    
    ensemble_model.fit(X_full, y_full)
    
    # --- d. Save the trained model object ---
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(ensemble_model, output_path)
    
    print(f"     ...Model training complete.")


# =============================================================================
# --- MAIN EXECUTION BLOCK ---
# =============================================================================
if __name__ == "__main__":
    start_time = time.time()
    print("--- Starting Daily Model Retraining Pipeline ---")

    try:
        # Step 1: Load and preprocess
        df_clean = load_and_preprocess_data(DATA_FILE_PATH)
        
        # Step 2: Create base features
        df_featured = create_base_features(df_clean)
        
        # Step 3: Create advanced features
        df_final_features = create_advanced_features(df_featured)
        
        # Step 4: Train and save the champion model
        model_output_path = os.path.join(MODEL_OUTPUT_DIR, MODEL_FILENAME)
        train_champion_model(df_final_features, model_output_path)
        
        end_time = time.time()
        
        print("\n--- PIPELINE COMPLETED SUCCESSFULLY ---")
        print(f"Final model saved to: {model_output_path}")
        print(f"Total runtime: {end_time - start_time:.2f} seconds")

    except FileNotFoundError:
        print(f"\nERROR: Input data file not found at '{DATA_FILE_PATH}'. Aborting pipeline.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the pipeline: {e}")