
'use client'; 

import { useState, useEffect } from 'react';


export default function HomePage() {
 
  const [todayAqi, setTodayAqi] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  

  const [lastUpdated, setLastUpdated] = useState(null);

  // This hook runs once when the component is first loaded.
  useEffect(() => {
    
    async function fetchAqiData() {
      const response = await fetch('https://qar-raz-aqi-predictor-qamar.hf.space/api/forecast');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch AQI forecast.');
      }
      return response.json();
    }
    
    async function fetchStatusData() {
      const response = await fetch('https://qar-raz-aqi-predictor-qamar.hf.space/api/status');
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch API status.');
      }
      return response.json();
    }

  
    async function loadAllData() {
      try {
       
        const [aqiData, statusData] = await Promise.all([
          fetchAqiData(),
          fetchStatusData()
        ]);

      
        setTodayAqi(aqiData.today);
        setForecast(aqiData.forecast);
        setLastUpdated(statusData.model_last_updated_utc); 
        // Set the new state

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadAllData();
  }, []); // The empty array [] means this effect runs only once.



  // A small helper function to format the long UTC date into a more readable format.
  const formatDate = (isoString) => {
    if (!isoString) return '';
    
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
      
      {/* Section for the 3-Day Forecast */}
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