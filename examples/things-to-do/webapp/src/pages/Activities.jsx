import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { askActivities, fetchActivities } from "../api";
import "../App.css";
import "./Activities.css";

export default function Activities() {
  const navigate = useNavigate();
  const { place, setActivity, setBooking, fromDate, toDate } = useCart();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [activities, setActivities] = useState([]);
  const [summary, setSummary] = useState("");
  const [expanded, setExpanded] = useState(null);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [tickets, setTickets] = useState(1);

  useEffect(() => {
    if (!place) return;
    setLoading(true);
    fetchActivities(place.id, fromDate, toDate)
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setActivities(list);
      })
      .catch(() => setSummary("Failed to load activities"))
      .finally(() => setLoading(false));
  }, [place?.id]);

  const handleSearch = async () => {
    if (!place) return;
    setLoading(true);
    try {
      const data = await askActivities(query || "things to do", place.id, fromDate, toDate);
      const payload = data.response || data;
      const list = Array.isArray(payload) ? payload : (payload.activities || []);
      setActivities(list);
      setSummary(payload.summary || "");
    } catch (err) {
      console.error(err);
      setSummary("Failed to get activities");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  const handleCardClick = (activity) => {
    if (expanded === activity.id) {
      setExpanded(null);
    } else {
      setExpanded(activity.id);
      setSelectedDate(activity.details?.[0]?.date || "");
      setSelectedTime(activity.details?.[0]?.times?.[0] || "");
      setTickets(1);
    }
  };

  const handleContinue = (activity) => {
    setActivity(activity);
    setBooking({ date: selectedDate, time: selectedTime, tickets });
    navigate("/addons");
  };

  const availableTimes = activities
    .find((a) => a.id === expanded)
    ?.details?.find((d) => d.date === selectedDate)?.times || [];

  if (!place) {
    return (
      <div className="app">
        <h2>Activities</h2>
        <p className="summary">No place selected. Please go back and choose a destination.</p>
        <button onClick={() => navigate("/")} className="continue-btn">Back to Discovery</button>
      </div>
    );
  }

  return (
    <div className="app">
      <h2>Activities in {place.name}</h2>

      <div className="search-bar">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Search activities..."
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {summary && <p className="summary">{summary}</p>}

      <div className="activities-list">
        {activities.map((activity) => {
          const isExpanded = expanded === activity.id;
          return (
            <div
              key={activity.id}
              className={`activity-card${isExpanded ? " activity-card--expanded" : ""}`}
            >
              <div
                className="activity-card-header"
                onClick={() => handleCardClick(activity)}
              >
                <div className="activity-card-info">
                  <h3 className="activity-card-name">{activity.name}</h3>
                  <div className="activity-card-meta">
                    <span className="activity-type-tag">{activity.type}</span>
                    <span>{activity.duration}</span>
                    <span className="activity-price">${activity.price_per_ticket.toFixed(2)} / ticket</span>
                  </div>
                </div>
                <span className="activity-expand-icon">{isExpanded ? "▲" : "▼"}</span>
              </div>

              {isExpanded && (
                <div className="activity-booking-panel">
                  <p className="activity-description">{activity.description}</p>

                  <div className="booking-fields">
                    <div className="filter-field">
                      <label>Date</label>
                      <select
                        value={selectedDate}
                        onChange={(e) => {
                          setSelectedDate(e.target.value);
                          const times = activity.details?.find((d) => d.date === e.target.value)?.times || [];
                          setSelectedTime(times[0] || "");
                        }}
                      >
                        {activity.details?.map((d) => (
                          <option key={d.date} value={d.date}>{d.date}</option>
                        ))}
                      </select>
                    </div>

                    <div className="filter-field">
                      <label>Time</label>
                      <select
                        value={selectedTime}
                        onChange={(e) => setSelectedTime(e.target.value)}
                      >
                        {availableTimes.map((t) => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                      </select>
                    </div>

                    <div className="filter-field">
                      <label>Tickets</label>
                      <div className="ticket-counter">
                        <button
                          className="ticket-btn"
                          onClick={() => setTickets((n) => Math.max(1, n - 1))}
                        >
                          −
                        </button>
                        <span className="ticket-count">{tickets}</span>
                        <button
                          className="ticket-btn"
                          onClick={() => setTickets((n) => n + 1)}
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="booking-total">
                    Total: ${(activity.price_per_ticket * tickets).toFixed(2)}
                  </div>

                  <button
                    className="continue-btn"
                    onClick={() => handleContinue(activity)}
                  >
                    Continue to Add-ons
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
