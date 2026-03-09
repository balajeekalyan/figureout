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
  const { flight, seats, addons, resetCart } = useCart();
  const [fees, setFees] = useState([]);
  const [feeQuery, setFeeQuery] = useState("");
  const [feeLoading, setFeeLoading] = useState(false);
  const [feeSummary, setFeeSummary] = useState("");

  useEffect(() => {
    if (!flight?.flight_number) return;
    fetchFees(flight.flight_number)
      .then((data) => setFees(data?.fees || []))
      .catch((err) => console.error("Failed to load fees", err));
  }, [flight?.flight_number]);

  const handleFeeSearch = async () => {
    if (!feeQuery.trim()) return;
    setFeeLoading(true);
    try {
      const data = await askFees(feeQuery, flight?.flight_number);
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

  if (!flight) {
    return (
      <div className="app">
        <h2>Booking Summary</h2>
        <div className="summary-card">
          <p className="summary-placeholder">
            No booking in progress. Start by searching for flights.
          </p>
        </div>
        <button onClick={() => navigate("/")} className="continue-btn">
          Back to Discovery
        </button>
      </div>
    );
  }

  const seatCount = seats.length || 1;
  const ticketTotal = flight.ticketPrice * seatCount;
  const seatTotal = seats.reduce((sum, s) => sum + (s.price || 0), 0);
  const addonTotal = addons.reduce((sum, a) => sum + (a.price || 0), 0);
  const subtotal = ticketTotal + seatTotal + addonTotal;
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
        <h3 className="summary-section-title">Flight</h3>
        <div className="summary-detail">
          <span>{flight.carrier_name}</span>
          <span className="summary-flight-number">{flight.flight_number}</span>
        </div>
        <div className="summary-detail">
          <span>{flight.source} → {flight.destination}</span>
        </div>
        <div className="summary-detail">
          <span>{flight.depart_date} at {flight.depart_time}</span>
        </div>
        <div className="summary-detail">
          <span>Class: {flight.tier}</span>
          <span>${flight.ticketPrice} / ticket</span>
        </div>
      </div>

      {seats.length > 0 && (
        <div className="summary-card">
          <h3 className="summary-section-title">Seats ({seats.length})</h3>
          {seats.map((s) => (
            <div className="summary-detail" key={s.seat_id}>
              <span>Seat {s.seat_id}</span>
              <span>{s.price === 0 ? "Included" : `$${s.price}`}</span>
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
              <span>${a.price}</span>
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
          <span>Tickets ({seatCount} x ${flight.ticketPrice})</span>
          <span>${ticketTotal.toFixed(2)}</span>
        </div>
        <div className="summary-detail">
          <span>Seat fees</span>
          <span>{seatTotal === 0 ? "Included" : `$${seatTotal.toFixed(2)}`}</span>
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
