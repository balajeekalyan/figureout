import React, { useState } from "react";
import { askDiscovery } from "../api";
import EventResults from "../EventResults";
import "../App.css";
import "./Discovery.css";

export default function Discovery() {
  const [query, setQuery] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState("");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setEvents([]);
    setSummary("");
    try {
      const data = await askDiscovery(query, fromDate, toDate, location);
      // Handle both verbose ({ response, debug }) and plain response
      const payload = data.response || data;
      // Multi-role: payload is role-keyed { role: { events, summary } }
      // Single-role: payload is { events, summary } or a flat array
      let eventList = [];
      const summaries = [];
      if (Array.isArray(payload)) {
        eventList = payload;
      } else if (payload.events) {
        eventList = payload.events;
        if (payload.summary) summaries.push(payload.summary);
      } else {
        // Role-keyed multi-role response — collect events from each role
        Object.values(payload).forEach((roleResult) => {
          if (roleResult?.events) eventList = eventList.concat(roleResult.events);
          if (roleResult?.summary) summaries.push(roleResult.summary);
        });
      }
      setEvents(eventList);
      setSummary(summaries.join(" | "));
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
      <h2>Discover Events</h2>

      <div className="discovery-bar">
        <div className="filter-field">
          <label htmlFor="fromDate">From</label>
          <input
            id="fromDate"
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
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
        <div className="filter-field">
          <label htmlFor="location">Location</label>
          <select
            id="location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          >
            <option value=""></option>
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
            placeholder="Search for concerts, artists, genres..."
          />
        </div>
        <button className="discovery-btn" onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {summary && <p className="summary">{summary}</p>}

      <EventResults events={events} />
    </div>
  );
}
