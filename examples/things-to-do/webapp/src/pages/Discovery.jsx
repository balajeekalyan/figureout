import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { askDiscovery } from "../api";
import PlacesResults from "../PlacesResults";
import "../App.css";
import "./Discovery.css";

export default function Discovery() {
  const navigate = useNavigate();
  const { setPlace, fromDate, setFromDate, toDate, setToDate } = useCart();
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("USA");
  const [loading, setLoading] = useState(false);
  const [places, setPlaces] = useState([]);
  const [summary, setSummary] = useState("");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await askDiscovery(query, fromDate, toDate, location);
      const payload = data.response || data;
      const list = Array.isArray(payload) ? payload : (payload.places || []);
      setPlaces(list);
      setSummary(payload.summary || "");
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

  const handleExplore = (place) => {
    setPlace(place);
    navigate("/activities");
  };

  return (
    <div className="app">
      <h2>Find Things To Do</h2>

      <div className="discovery-bar">
        <div className="filter-field">
          <label htmlFor="from-date">From</label>
          <input
            id="from-date"
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
          />
        </div>
        <div className="filter-field">
          <label htmlFor="to-date">To</label>
          <input
            id="to-date"
            type="date"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
          />
        </div>
        <div className="filter-field">
          <label htmlFor="location">Location</label>
          <select
            id="location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          >
            <option value="USA">USA</option>
            <option value="UK">UK</option>
          </select>
        </div>
        <div className="filter-field filter-field-search">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="What do you want to do?"
          />
        </div>
        <button className="discovery-btn" onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {summary && <p className="summary">{summary}</p>}

      <PlacesResults places={places} onExplore={handleExplore} />
    </div>
  );
}
