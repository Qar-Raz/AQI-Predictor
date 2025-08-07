// This is a special Next.js directive. It tells Next.js that this component
// needs to run in the browser, which is required for fetching data and managing state.
'use client'; 

import { useState, useEffect } from 'react';

// This is your main page component.
export default function HomePage() {
  // --- State Variables ---
  // We use 'useState' to store data that can change over time.
  // When this data changes, the component will automatically re-render.

  // 'forecast' will store the prediction data we get from the API.
  const [forecast, setForecast] = useState(null);
  
  // 'loading' will be true while we are waiting for the API response.
  const [loading, setLoading] = useState(true);

  // 'error' will store any error message if the API call fails.
  const [error, setError] = useState(null);

  // --- Data Fetching Logic ---
  // 'useEffect' is a special hook that runs code after the component has rendered.
  // By providing an empty array `[]` at the end, we tell it to run only ONCE.
  useEffect(() => {
    // This is the main function to fetch data from our FastAPI backend.
    async function fetchForecast() {
      try {
        // The URL of your running FastAPI server.
        const response = await fetch('http://127.0.0.1:8000/forecast');
        
        // If the server responded with an error (e.g., 500), throw an error.
        if (!response.ok) {
          throw new Error('Failed to fetch forecast from the server.');
        }
        
        // Parse the JSON response from the server.
        const data = await response.json();
        
        // Store the forecast data in our state variable.
        setForecast(data.forecast);
      } catch (err) {
        // If anything goes wrong, store the error message.
        setError(err.message);
      } finally {
        // No matter what happens, set loading to false once we're done.
        setLoading(false);
      }
    }

    // Call the function we just defined.
    fetchForecast();
  }, []); // The empty array `[]` means this effect runs only once.

  // --- UI Rendering Logic ---
  // This section determines what the user sees on the screen.

  // While the data is loading, show a simple message.
  if (loading) {
    return <main className="container"><p>Loading forecast...</p></main>;
  }

  // If an error occurred, show the error message.
  if (error) {
    return <main className="container"><p>Error: {error}</p></main>;
  }

  // If we have the data, display it.
  return (
    <main className="container">
      <div className="header">
        <h1>Karachi AQI Forecast</h1>
        <p>3-Day Air Quality Index Prediction</p>
      </div>
      
      <ul className="forecast-list">
        {forecast && forecast.map((day) => (
          // We loop over the forecast array and create a list item for each day.
          // The 'key' is a special React requirement for lists.
          <li key={day.date} className="forecast-item">
            <span className="date">{day.date}</span>
            <span className="aqi">{day.predicted_aqi} AQI</span>
          </li>
        ))}
      </ul>
    </main>
  );
}