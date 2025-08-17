// This is a special Next.js directive. It tells Next.js that this component
// needs to run in the browser, which is required for fetching data and managing state.
'use client'; 

import { useState, useEffect } from 'react';

// This is your main page component.
export default function HomePage() {
  // --- State Variables ---
  // We now have a separate state for 'todayAqi' to hold the current day's data.
  const [todayAqi, setTodayAqi] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- Data Fetching Logic (useEffect) ---
  // This hook runs once when the component is first loaded.
  useEffect(() => {
    async function fetchForecast() {
      try {
        const response = await fetch('https://qar-raz-aqi-predictor-qamar.hf.space/api/forecast');
        
        if (!response.ok) {
          // Try to get a more detailed error from the server's response
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch forecast from the server.');
        }
        
        const data = await response.json();
        
        // --- THIS IS THE KEY CHANGE ---
        // We now populate both state variables from the new API response structure.
        setTodayAqi(data.today);
        setForecast(data.forecast);

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchForecast();
  }, []); // The empty array `[]` means this effect runs only once.

  // --- UI Rendering Logic ---

  if (loading) {
    return <main className="container"><p>Loading forecast...</p></main>;
  }

  if (error) {
    return <main className="container"><p style={{ color: '#ff8a80' }}>Error: {error}</p></main>;
  }

  return (
    <main className="container">
      <div className="header">
        <h1>Karachi AQI</h1>
        <p>Live Data & 3-Day Forecast</p>
      </div>

      {/* === Section for Today's AQI (Large Label) === */}
      {/* This checks if todayAqi has data before trying to render it. */}
      {todayAqi && (
        <div className="today-aqi-container">
          <div className="today-aqi-value">{todayAqi.aqi}</div>
          <div className="today-aqi-label">{"Today's AQI (" + todayAqi.date + ")"}</div>
        </div>
      )}
      
      {/* --- Section for the 3-Day Forecast --- */}
      <h2 className="forecast-title">Next 3 Days Forecast</h2>
      <ul className="forecast-list">
        {forecast && forecast.map((day) => (
          <li key={day.date} className="forecast-item">
            <span className="date">{day.date}</span>
            <span className="aqi">{day.predicted_aqi} AQI</span>
          </li>
        ))}
      </ul>
    </main>
  );
}