from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import ONLY the new master function from your prediction.py file
from .prediction import generate_full_response

# --- 1. Initialize the FastAPI App ---
app = FastAPI(
    title="Pearls AQI Predictor API",
    description="An API to provide today's AQI and a 3-day forecast.",
    version="1.0.0"
)

# --- 2. Set up CORS ---
origins = [
    "http://localhost:3000",
    "localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Define the Prediction Endpoint ---
@app.get("/forecast")
def get_aqi_forecast():
    """
    This endpoint runs the complete prediction pipeline to get today's
    AQI value and a 3-day future forecast.
    """
    print("--- Received request for /forecast ---")
    
    # Call the single, powerful function from prediction.py
    response_data = generate_full_response()
    
    # Handle any errors that the function might have returned
    if "error" in response_data:
        raise HTTPException(status_code=500, detail=response_data["error"])
        
    return response_data

# --- 4. Define a Root Endpoint ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the AQI Predictor API."}