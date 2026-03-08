import React from "react";
import "./SeatMap.css";

const SECTIONS = [
  { id: "F", label: "Front", rows: 3, cols: 12 },
  { id: "M", label: "Middle", rows: 4, cols: 14 },
  { id: "B", label: "Back", rows: 4, cols: 16 },
];

const ROW_LABELS = ["A", "B", "C", "D"];

export default function SeatMap({ selectedSeats, onSeatClick, soldSeats = [], recommendedSeats = [] }) {
  const isSelected = (id) => selectedSeats.includes(id);
  const isSold = (id) => soldSeats.includes(id);
  const isRecommended = (id) => !isSelected(id) && recommendedSeats.includes(id);

  return (
    <div className="seat-map">
      <div className="stage">STAGE</div>

      {SECTIONS.map((section) => (
        <div key={section.id} className="section">
          <div className="section-label">{section.label}</div>
          <div className="seats-container">
            {Array.from({ length: section.rows }, (_, r) => {
              const rowLabel = ROW_LABELS[r];
              return (
                <div key={rowLabel} className="seat-row">
                  <span className="row-label">{rowLabel}</span>
                  {Array.from({ length: section.cols }, (_, c) => {
                    const col = c + 1;
                    const seatId = `${section.id}${col}`;
                    // Only render unique seat IDs for first row to avoid duplicates
                    // Use row-aware IDs for multi-row sections
                    const fullId = `${section.id}${rowLabel}${col}`;
                    const selected = isSelected(fullId);
                    const sold = isSold(fullId);
                    const recommended = isRecommended(fullId);
                    return (
                      <div
                        key={fullId}
                        className={`seat ${selected ? "selected" : ""} ${recommended ? "recommended" : ""} ${sold ? "sold" : ""}`}
                        onClick={() => !sold && onSeatClick(fullId)}
                        title={sold ? `${fullId} (Sold)` : recommended ? `${fullId} (Recommended)` : fullId}
                      >
                        {col}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      ))}

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
          <span className="seat-sample recommended"></span>
          <span>Recommended</span>
        </div>
        <div className="legend-item">
          <span className="seat-sample sold"></span>
          <span>Sold</span>
        </div>
      </div>
    </div>
  );
}
