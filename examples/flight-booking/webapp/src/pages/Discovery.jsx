import React, { useState } from "react";
import { askDiscovery } from "../api";
import FlightResults from "../FlightResults";
import "../App.css";
import "./Discovery.css";

export default function Discovery() {
  const [query, setQuery] = useState("");
  const [date, setDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [summary, setSummary] = useState("");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await askDiscovery(query, date, toDate);
      setResponse(data);
      setSummary(data.summary || "");
    } catch (err) {
      console.error(err);
      setSummary("Failed to get recommendations");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="app">
      <h2>Find a Flight</h2>

      <div className="discovery-bar">
        <div className="filter-field">
          <label htmlFor="date">From</label>
          <input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <div className="filter-field">
          <label htmlFor="toDate">To</label>
          <input
            id="toDate"
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
          />
        </div>
        <div className="filter-field filter-field-search">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search for flights..."
          />
        </div>
        <button className="discovery-btn" onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {summary && <p className="summary">{summary}</p>}

      {response && response.flights && (
        <FlightResults flights={response.flights} />
      )}
    </div>
  );
}
