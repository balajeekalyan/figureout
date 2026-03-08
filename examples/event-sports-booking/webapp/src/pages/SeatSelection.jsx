import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { getSeats, askSeatSelection } from "../api";
import SeatMap from "../SeatMap";
import "../App.css";

const SECTION_MAP = {
  F: "Front",
  M: "Middle",
  B: "Back",
};

export default function SeatSelection() {
  const navigate = useNavigate();
  const { event, setSeats: setCartSeats } = useCart();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [recommendedSeats, setRecommendedSeats] = useState([]);
  const [summary, setSummary] = useState("");
  const [seatData, setSeatData] = useState(null);
  const [soldSeats, setSoldSeats] = useState([]);

  const normalizeSeatId = (raw) => {
    if (!raw) return null;
    const s = String(raw).trim().toUpperCase();
    // Try exact match from loaded seat data
    if (seatData?.section?.rows) {
      const match = seatData.section.rows.find(
        (r) => r.seat_id.toUpperCase() === s
      );
      if (match) return match.seat_id;
    }
    // Fall back to raw value — seat_id came from the tool so it's valid
    return s;
  };

  useEffect(() => {
    if (!event?.id) {
      navigate("/");
      return;
    }
    const fetchSeats = async () => {
      try {
        const data = await getSeats(event.id);
        setSeatData(data);
        const sold = (data?.section?.rows || [])
          .filter((r) => r.status === "sold")
          .map((r) => r.seat_id);
        setSoldSeats(sold);
      } catch (err) {
        console.error("Failed to load seat data:", err);
      }
    };
    fetchSeats();
  }, [event?.id]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await askSeatSelection(query, event?.id);
      console.log("[SeatSelection] raw response:", data);
      const payload = data.response || data;
      setSummary(payload.summary || "");
      const recs = payload.recommendations || [];
      console.log("[SeatSelection] recommendations:", recs);
      if (recs.length > 0) {
        const top4 = recs
          .slice(0, 4)
          .map((r) => normalizeSeatId(r.seat_id))
          .filter((id) => id && !soldSeats.includes(id));
        console.log("[SeatSelection] normalized top4:", top4);
        if (top4.length > 0) {
          setRecommendedSeats(top4);
        }
      }
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

  const handleSeatClick = (seatId) => {
    if (soldSeats.includes(seatId)) return;
    setSelectedSeats((prev) =>
      prev.includes(seatId)
        ? prev.filter((s) => s !== seatId)
        : [...prev, seatId]
    );
  };

  const handleContinue = () => {
    const rows = seatData?.section?.rows || [];
    const cartSeats = selectedSeats.map((id) => {
      const row = rows.find((r) => r.seat_id === id);
      return {
        seat_id: id,
        section: SECTION_MAP[id.charAt(0)] || "Unknown",
        price: row ? row.price : 0,
      };
    });
    setCartSeats(cartSeats);
    navigate("/addons");
  };

  return (
    <div className="app">
      <h2>Seat Selection</h2>

      <div className="search-bar">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask for seat recommendations..."
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {summary && <p className="summary">{summary}</p>}

      <SeatMap
        selectedSeats={selectedSeats}
        onSeatClick={handleSeatClick}
        soldSeats={soldSeats}
        recommendedSeats={recommendedSeats}
      />

      <button
        onClick={handleContinue}
        disabled={selectedSeats.length === 0}
        className="continue-btn"
      >
        Continue to Add-ons ({selectedSeats.length} seat
        {selectedSeats.length !== 1 ? "s" : ""})
      </button>
    </div>
  );
}
