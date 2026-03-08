import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { fetchFees, askFees } from "../api";
import "../App.css";
import "./Summary.css";

function calcFeeAmount(fee, subtotal) {
  const raw = fee.amount.trim();
  if (raw.endsWith("%")) return subtotal * (parseFloat(raw) / 100);
  if (raw.startsWith("$")) return parseFloat(raw.slice(1));
  return parseFloat(raw) || 0;
}

export default function Summary() {
  const navigate = useNavigate();
  const { event, seats, addons, resetCart } = useCart();
  const [fees, setFees] = useState([]);
  const [feeQuery, setFeeQuery] = useState("");
  const [feeLoading, setFeeLoading] = useState(false);
  const [feeSummary, setFeeSummary] = useState("");

  useEffect(() => {
    if (!event?.id) return;
    fetchFees(event.id)
      .then((data) => setFees(data?.fees || []))
      .catch((err) => console.error("Failed to load fees", err));
  }, [event?.id]);

  const handleFeeSearch = async () => {
    if (!feeQuery.trim()) return;
    setFeeLoading(true);
    try {
      const data = await askFees(feeQuery, event?.id);
      const payload = data.response || data;
      setFeeSummary(payload.summary || "");
    } catch (err) {
      console.error(err);
      setFeeSummary("Failed to get fee explanation");
    } finally {
      setFeeLoading(false);
    }
  };

  const handleFeeKeyDown = (e) => {
    if (e.key === "Enter") handleFeeSearch();
  };

  if (!event) {
    return (
      <div className="app">
        <h2>Booking Summary</h2>
        <div className="summary-card">
          <p className="summary-placeholder">
            No booking in progress. Start by searching for events.
          </p>
        </div>
        <button onClick={() => navigate("/")} className="continue-btn">
          Back to Discovery
        </button>
      </div>
    );
  }

  const seatTotal = seats.reduce((sum, s) => sum + (s.price || 0), 0);
  const addonTotal = addons.reduce((sum, a) => sum + (a.price || 0), 0);
  const subtotal = seatTotal + addonTotal;
  const feeLineItems = fees.map((fee) => ({
    ...fee,
    computed: calcFeeAmount(fee, subtotal),
  }));
  const feesTotal = feeLineItems.reduce((sum, f) => sum + f.computed, 0);
  const grandTotal = subtotal + feesTotal;

  return (
    <div className="app">
      <h2>Booking Summary</h2>

      <div className="summary-card">
        <h3 className="summary-section-title">Event</h3>
        {event.name && (
          <div className="summary-detail">
            <span>Event</span>
            <span>{event.name}</span>
          </div>
        )}
        {event.artist && event.artist !== event.name && (
          <div className="summary-detail">
            <span>Artist</span>
            <span>{event.artist}</span>
          </div>
        )}
        {event.type && (
          <div className="summary-detail">
            <span>Type</span>
            <span>{event.type}</span>
          </div>
        )}
        {event.date && (
          <div className="summary-detail">
            <span>Date</span>
            <span>{event.date}</span>
          </div>
        )}
        {event.showtime && (
          <div className="summary-detail">
            <span>Showtime</span>
            <span>{event.showtime}</span>
          </div>
        )}
        {(event.city || event.location) && (
          <div className="summary-detail">
            <span>Location</span>
            <span>
              {event.city}
              {event.country ? `, ${event.country}` : ""}
              {!event.city && event.location ? event.location : ""}
            </span>
          </div>
        )}
      </div>

      {seats.length > 0 && (
        <div className="summary-card">
          <h3 className="summary-section-title">Seats ({seats.length})</h3>
          {seats.map((s) => (
            <div className="summary-detail" key={s.seat_id}>
              <span>Seat {s.seat_id} ({s.section})</span>
              <span>${s.price.toFixed(2)}</span>
            </div>
          ))}
        </div>
      )}

      {addons.length > 0 && (
        <div className="summary-card">
          <h3 className="summary-section-title">Add-ons</h3>
          {addons.map((a) => (
            <div className="summary-detail" key={a.name}>
              <span>{a.name}</span>
              <span>${a.price.toFixed(2)}</span>
            </div>
          ))}
        </div>
      )}

      <div className="search-bar">
        <input
          type="text"
          value={feeQuery}
          onChange={(e) => setFeeQuery(e.target.value)}
          onKeyDown={handleFeeKeyDown}
          placeholder="Ask about fees..."
        />
        <button onClick={handleFeeSearch} disabled={feeLoading}>
          {feeLoading ? "Asking..." : "Ask"}
        </button>
      </div>

      {feeSummary && <p className="summary">{feeSummary}</p>}

      <div className="summary-card summary-totals">
        <h3 className="summary-section-title">Price Breakdown</h3>
        <div className="summary-detail">
          <span>Seats ({seats.length})</span>
          <span>${seatTotal.toFixed(2)}</span>
        </div>
        {addonTotal > 0 && (
          <div className="summary-detail">
            <span>Add-ons</span>
            <span>${addonTotal.toFixed(2)}</span>
          </div>
        )}
        <div className="summary-detail">
          <span>Subtotal</span>
          <span>${subtotal.toFixed(2)}</span>
        </div>
        {feeLineItems.map((fee) => (
          <div className="summary-detail" key={fee.type}>
            <span>{fee.type} ({fee.amount})</span>
            <span>${fee.computed.toFixed(2)}</span>
          </div>
        ))}
        <div className="summary-detail summary-grand-total">
          <span>Total</span>
          <span>${grandTotal.toFixed(2)}</span>
        </div>
      </div>

      <button
        onClick={() => {
          resetCart();
          navigate("/");
        }}
        className="continue-btn"
      >
        Start New Booking
      </button>
    </div>
  );
}
