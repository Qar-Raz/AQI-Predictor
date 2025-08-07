from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import the main prediction function from your prediction.py file
from .prediction import generate_forecast_from_files

# --- 1. Initialize the FastAPI App ---
app = FastAPI(
    title="AQI Predictor API",
    description="An app to forecast the Air Quality Index in Karachi (AQI) for the next 3 days.",
    version="1.0.0"
)

# --- 2. Set up CORS (Cross-Origin Resource Sharing) ---
# This is CRITICAL for your Next.js frontend to be able to call the API
# from the browser during development.
origins = [
    "http://localhost:3000",  # Default port for Next.js
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# this @ is a decorator that tells the function to run when the user visits the /forecast endpoint
# We are making a url which is called an endpoint which will be used to call the prediction pipeline
@app.get("/forecast")
def get_aqi_forecast():
    print("Received request for /forecast")
    
    # Call the function you already built and tested
    forecast_result = generate_forecast_from_files()
    
    # Error handling: If the prediction function returned an error,
    # return a proper HTTP error to the client.
    if "error" in forecast_result:
        raise HTTPException(status_code=500, detail=forecast_result["error"])
        
        # note our method actually returns a dictionary, but frontend needs a json, so it is automatically converted to json by fastapi
    return forecast_result


# --- 4. Define a Root Endpoint (Good for Health Checks) ---
@app.get("/")
def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the AQI Predictor API. Go to /docs to see the API documentation."}