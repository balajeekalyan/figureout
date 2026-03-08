import React from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "./CartContext";
import "./EventResults.css";

const TICKET_PRICES = {
  Front: 150,
  Middle: 95,
  Back: 55,
};

function EventSpecificDetails({ details, type }) {
  if (!details) return null;

  const entries = Object.entries(details).filter(
    ([, value]) => value && value !== "N/A" && value !== "Unknown"
  );
  if (entries.length === 0) return null;

  const labelMap = {
    rating: "Rating",
    runtime: "Runtime",
    synopsis: "Synopsis",
    age_range: "Ages",
    duration: "Duration",
    description: "Description",
    venue: "Venue",
    tour_name: "Tour",
    lineup_highlights: "Lineup",
    duration_days: "Days",
    league: "League",
  };

  return (
    <div className="event-specific-details">
      {entries.map(([key, value]) => {
        const label = labelMap[key] || key.replace(/_/g, " ");
        const displayValue = Array.isArray(value) ? value.join(", ") : value;
        return (
          <div className="event-specific-row" key={key}>
            <span className="event-specific-label">{label}</span>
            <span className="event-specific-value">{displayValue}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function EventResults({ events }) {
  const navigate = useNavigate();
  const { setEvent } = useCart();

  if (!events || events.length === 0) return null;

  const handleShowtimeClick = (event, detail, showtime) => {
    setEvent({
      id: event.event_id,
      name: event.name,
      artist: event.artist,
      type: event.type,
      genre: event.genre,
      date: detail.date,
      city: detail.city,
      country: detail.country,
      showtime,
      ticketPrices: TICKET_PRICES,
    });
    navigate("/seat-selection");
  };

  return (
    <div className="event-results">
      {events.map((event) => (
        <div className="event-card" key={event.event_id || event.name}>
          <div className="event-header">
            <h3 className="event-name">{event.name}</h3>
            <span className="event-type">{event.type}</span>
          </div>
          {event.artist && event.artist !== event.name && (
            <p className="event-artist">{event.artist}</p>
          )}
          {event.genre && event.genre.length > 0 && (
            <div className="event-genres">
              {event.genre.map((g) => (
                <span className="event-genre-tag" key={g}>{g}</span>
              ))}
            </div>
          )}
          <EventSpecificDetails
            details={event.event_specific_details}
            type={event.type}
          />
          {event.details && event.details.length > 0 && (
            <div className="event-details">
              {event.details.map((detail, di) => (
                <div className="event-detail-row" key={di}>
                  <div className="event-detail-info">
                    <span className="event-detail-date">{detail.date}</span>
                    <span className="event-detail-location">
                      {detail.city}{detail.country ? `, ${detail.country}` : ""}
                    </span>
                  </div>
                  <div className="event-showtimes">
                    {detail.showtimes.map((st) => (
                      <button
                        className="event-showtime-btn"
                        key={st}
                        onClick={() => handleShowtimeClick(event, detail, st)}
                      >
                        {st}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
