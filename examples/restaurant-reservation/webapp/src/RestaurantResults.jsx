import React from "react";
import "./RestaurantResults.css";

export default function RestaurantResults({ restaurants, onSelectTime }) {
  if (!restaurants || restaurants.length === 0) return null;

  return (
    <div className="restaurant-results">
      {restaurants.map((r, index) => (
        <div className="restaurant-card" key={r.id || index}>
          <div className="restaurant-card-header">
            <h3 className="restaurant-card-name">{r.name}</h3>
            <div className="restaurant-card-meta">
              <span>{r.cuisine}</span>
              {r.type && <span>{r.type}</span>}
            </div>
          </div>
          {r.dietary_options?.length > 0 && (
            <div className="restaurant-card-tags">
              {r.dietary_options.map((opt, i) => (
                <span className="restaurant-tag" key={i}>{opt}</span>
              ))}
            </div>
          )}
          {r.details?.map((detail, di) => (
            <div className="restaurant-detail" key={di}>
              <div className="restaurant-detail-info">
                {detail.date && <span>{detail.date}</span>}
                {detail.city && <span>{detail.city}</span>}
                {detail.hours && <span>{detail.hours}</span>}
              </div>
              {detail.reservations?.length > 0 && (
                <div className="restaurant-times">
                  {detail.reservations.map((time, ti) => (
                    <button
                      key={ti}
                      className="restaurant-time-btn"
                      onClick={() => onSelectTime(r, detail, time)}
                    >
                      {time}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
