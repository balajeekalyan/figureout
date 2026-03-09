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
  const { reservation, addons, resetCart } = useCart();
  const [fees, setFees] = useState([]);
  const [feeQuery, setFeeQuery] = useState("");
  const [feeLoading, setFeeLoading] = useState(false);
  const [feeSummary, setFeeSummary] = useState("");

  useEffect(() => {
    if (!reservation?.restaurant_id) return;
    fetchFees(reservation.restaurant_id)
      .then((data) => setFees(data?.fees || []))
      .catch((err) => console.error("Failed to load fees", err));
  }, [reservation?.restaurant_id]);

  const handleFeeSearch = async () => {
    if (!feeQuery.trim()) return;
    setFeeLoading(true);
    try {
      const data = await askFees(feeQuery, reservation?.restaurant_id);
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

  if (!reservation) {
    return (
      <div className="app">
        <h2>Reservation Summary</h2>
        <div className="summary-card">
          <p className="summary-placeholder">
            No reservation in progress. Start by searching for restaurants.
          </p>
        </div>
        <button onClick={() => navigate("/")} className="continue-btn">
          Back to Discovery
        </button>
      </div>
    );
  }

  const subtotal = addons.reduce((sum, a) => sum + (a.price || 0), 0);
  const feeLineItems = fees.map((fee) => ({
    ...fee,
    computed: calcFeeAmount(fee, subtotal),
  }));
  const feesTotal = feeLineItems.reduce((sum, f) => sum + f.computed, 0);
  const grandTotal = subtotal + feesTotal;

  return (
    <div className="app">
      <h2>Reservation Summary</h2>

      <div className="summary-card">
        <h3 className="summary-section-title">Reservation</h3>
        {reservation.restaurant && (
          <div className="summary-detail">
            <span>Restaurant</span>
            <span>{reservation.restaurant}</span>
          </div>
        )}
        {reservation.time && (
          <div className="summary-detail">
            <span>Time</span>
            <span>{reservation.time}</span>
          </div>
        )}
        {reservation.date && (
          <div className="summary-detail">
            <span>Date</span>
            <span>{reservation.date}</span>
          </div>
        )}
        {reservation.location && (
          <div className="summary-detail">
            <span>Location</span>
            <span>{reservation.location}</span>
          </div>
        )}
      </div>

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
        Start New Search
      </button>
    </div>
  );
}
