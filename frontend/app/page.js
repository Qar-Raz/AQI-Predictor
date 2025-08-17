// This is a special Next.js directive. It tells Next.js that this component
// needs to run in the browser, which is required for fetching data and managing state.
'use client'; 

import { useState, useEffect } from 'react';

// This is your main page component.
export default function HomePage() {
  // --- State Variables ---
  const [todayAqi, setTodayAqi] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // NEW STATE VARIABLE: To hold the "last updated" timestamp from the status endpoint.
  const [lastUpdated, setLastUpdated] = useState(null);

  // --- Data Fetching Logic (useEffect) ---
  // This hook runs once when the component is first loaded.
  useEffect(() => {
    // We now have two separate functions to fetch our data for clarity.
    async function fetchAqiData() {
      const response = await fetch('https://qar-raz-aqi-predictor-qamar.hf.space/api/forecast');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch AQI forecast.');
      }
      return response.json();
    }
    
    // NEW FETCH FUNCTION: To get the backend's status.
    async function fetchStatusData() {
      const response = await fetch('https://qar-raz-aqi-predictor-qamar.hf.space/api/status');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch API status.');
      }
      return response.json();
    }

    // This new master function will run both fetches at the same time for efficiency.
    async function loadAllData() {
      try {
        // Promise.all is the most efficient way to run multiple fetches concurrently.
        const [aqiData, statusData] = await Promise.all([
          fetchAqiData(),
          fetchStatusData()
        ]);

        // Populate all our state variables with the results from both fetches.
        setTodayAqi(aqiData.today);
        setForecast(aqiData.forecast);
        setLastUpdated(statusData.model_last_updated_utc); // Set the new state

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadAllData();
  }, []); // The empty array `[]` means this effect runs only once.

  // --- UI Rendering Logic ---

  // A small helper function to format the long UTC date into a more readable format.
  const formatDate = (isoString) => {
    if (!isoString) return '';
    // This will format the date like "August 17, 2025, 10:30 PM" in the user's local timezone.
    return new Date(isoString).toLocaleString(undefined, {
      dateStyle: 'long',
      timeStyle: 'short',
    });
  };

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
      
      {/* NEW UI ELEMENT: The "Last Updated" label. */}
      {/* This checks if 'lastUpdated' has data before trying to render it. */}
      {lastUpdated && (
        <div className="last-updated-label">
          Model Last Updated: {formatDate(lastUpdated)}
        </div>
      )}

      {/* === Section for Today's AQI (Large Label) === */}
      {/* This checks if todayAqi has data before trying to render it. */}
      {todayAqi && (
        <div className="today-aqi-container">
          <div className="today-aqi-value">{todayAqi.aqi}</div>
          <div className="today-aqi-label">
            {/* This creates a YYYY-MM-DD formatted date for right now */}
            {"Today's AQI (" + new Date().toLocaleDateString('en-CA') + ")"}
          </div>
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