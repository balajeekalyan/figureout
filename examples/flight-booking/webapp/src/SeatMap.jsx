import React from "react";
import "./SeatMap.css";

const ROWS = Array.from({ length: 20 }, (_, i) => i + 1);
const LEFT_COLS = ["A", "B", "C"];
const RIGHT_COLS = ["D", "E", "F"];

export default function SeatMap({ selectedSeats, onSeatClick, soldSeats = [] }) {
  const isSelected = (id) => selectedSeats.includes(id);
  const isSold = (id) => soldSeats.includes(id);

  return (
    <div className="seat-map">
      <div className="cockpit">FRONT</div>

      <div className="col-headers">
        <span className="row-number-spacer"></span>
        {LEFT_COLS.map((c) => (
          <span key={c} className="col-label">{c}</span>
        ))}
        <span className="aisle-label">aisle</span>
        {RIGHT_COLS.map((c) => (
          <span key={c} className="col-label">{c}</span>
        ))}
      </div>

      <div className="seats-container">
        {ROWS.map((row) => (
          <div key={row} className="seat-row">
            <span className="row-number">{row}</span>
            {LEFT_COLS.map((col) => {
              const seatId = `${row}${col}`;
              const selected = isSelected(seatId);
              const sold = isSold(seatId);
              return (
                <div
                  key={seatId}
                  className={`seat ${selected ? "selected" : ""} ${sold ? "sold" : ""}`}
                  onClick={() => !sold && onSeatClick(seatId)}
                  title={sold ? `${seatId} (Sold)` : seatId}
                >
                  {col}
                </div>
              );
            })}
            <div className="aisle"></div>
            {RIGHT_COLS.map((col) => {
              const seatId = `${row}${col}`;
              const selected = isSelected(seatId);
              const sold = isSold(seatId);
              return (
                <div
                  key={seatId}
                  className={`seat ${selected ? "selected" : ""} ${sold ? "sold" : ""}`}
                  onClick={() => !sold && onSeatClick(seatId)}
                  title={sold ? `${seatId} (Sold)` : seatId}
                >
                  {col}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <div className="seat-legend">
        <div className="legend-item">
          <span className="seat-sample available"></span>
          <span>Available</span>
        </div>
        <div className="legend-item">
          <span className="seat-sample selected"></span>
          <span>Selected</span>
        </div>
        <div className="legend-item">
          <span className="seat-sample sold"></span>
          <span>Sold</span>
        </div>
      </div>
    </div>
  );
}
