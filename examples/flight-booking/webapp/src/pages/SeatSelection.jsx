import React, { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getSeats, askSeatSelection } from "../api";
import { useCart } from "../CartContext";
import SeatMap from "../SeatMap";
import "../App.css";

export default function SeatSelection() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setSeats: setCartSeats } = useCart();
  const flightNumber = searchParams.get("flight") || "";
  const tier = searchParams.get("class") || "";

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [soldSeats, setSoldSeats] = useState([]);
  const [seatData, setSeatData] = useState(null);
  const [summary, setSummary] = useState("");

  const normalizeSeatId = (raw) => {
    if (!raw) return null;
    const s = String(raw).trim();
    // Try direct match from seat data
    if (seatData?.section?.rows) {
      const match = seatData.section.rows.find(
        (r) => r.seat_id === s || String(r.row) === s || String(r.column) === s
      );
      if (match) return match.seat_id;
    }
    // Extract row number + column letter from any format
    const digits = s.match(/\d+/);
    const letter = s.match(/[A-Za-z]/);
    if (digits && letter) {
      const row = parseInt(digits[0]);
      const col = letter[0].toUpperCase();
      if (row >= 1 && row <= 20 && col >= "A" && col <= "F") {
        return `${row}${col}`;
      }
    }
    return null;
  };

  useEffect(() => {
    if (!flightNumber) return;
    const fetchSeats = async () => {
      try {
        const data = await getSeats(flightNumber, tier);
        setSeatData(data);
        const sold = (data.section?.rows || [])
          .filter((r) => r.status === "sold")
          .map((r) => r.seat_id);
        setSoldSeats(sold);
      } catch (err) {
        console.error(err);
      }
    };
    fetchSeats();
  }, [flightNumber, tier]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await askSeatSelection(query, flightNumber, tier);
      const data = res?.response || res;
      setSummary(data?.summary || "");
      const recs = data?.recommendations || [];
      if (recs.length > 0) {
        const top4 = recs
          .slice(0, 4)
          .map((r) => normalizeSeatId(r.seat_id || r.row))
          .filter((id) => id && !soldSeats.includes(id));
        if (top4.length > 0) {
          setSelectedSeats(top4);
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

  return (
    <div className="app">
      <h2>Seat Selection</h2>
      {flightNumber && (
        <p className="summary">
          Flight: {flightNumber}{tier ? ` — ${tier}` : ""}
        </p>
      )}

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
      />

      <button
        onClick={() => {
          const rows = seatData?.section?.rows || [];
          const cartSeats = selectedSeats.map((id) => {
            const row = rows.find((r) => r.seat_id === id);
            return { seat_id: id, price: row ? row.price : 0 };
          });
          setCartSeats(cartSeats);
          navigate("/addons");
        }}
        disabled={selectedSeats.length === 0}
        className="continue-btn"
      >
        Continue to Add-ons ({selectedSeats.length} seat
        {selectedSeats.length !== 1 ? "s" : ""})
      </button>
    </div>
  );
}
