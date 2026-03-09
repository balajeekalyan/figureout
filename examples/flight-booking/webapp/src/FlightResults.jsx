import React from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "./CartContext";
import "./FlightResults.css";

export default function FlightResults({ flights }) {
  const navigate = useNavigate();
  const { setFlight } = useCart();

  if (!flights || flights.length === 0) return null;

  const handlePriceClick = (flight, priceObj) => {
    setFlight({
      flight_number: flight.flight_number,
      carrier_name: flight.carrier_name,
      source: `${flight.source_airport_code} — ${flight.source_city}`,
      destination: `${flight.destination_airport_code} — ${flight.destination_city}`,
      depart_date: flight.depart_date,
      depart_time: flight.depart_time,
      tier: priceObj.class,
      ticketPrice: priceObj.price_per_seat,
    });
    navigate(
      `/seat-selection?flight=${encodeURIComponent(flight.flight_number)}&class=${encodeURIComponent(priceObj.class)}`
    );
  };

  return (
    <div className="flight-results">
      {flights.map((flight, index) => (
        <div className="flight-card" key={index}>
          <div className="flight-header">
            <h3 className="flight-carrier">{flight.carrier_name}</h3>
            <span className="flight-number">{flight.flight_number}</span>
          </div>
          <div className="flight-route">
            <div className="flight-endpoint">
              <span className="flight-airport">{flight.source_airport_code}</span>
              <span className="flight-city">{flight.source_city}</span>
              <span className="flight-datetime">{flight.depart_date} {flight.depart_time}</span>
            </div>
            <div className="flight-arrow">→</div>
            <div className="flight-endpoint">
              <span className="flight-airport">{flight.destination_airport_code}</span>
              <span className="flight-city">{flight.destination_city}</span>
              <span className="flight-datetime">{flight.arrival_date} {flight.arrival_time}</span>
            </div>
          </div>
          {flight.price && flight.price.length > 0 && (
            <div className="flight-prices">
              {flight.price.map((p, i) => (
                <button
                  className="flight-price-link"
                  key={i}
                  onClick={() => handlePriceClick(flight, p)}
                >
                  {p.class}: ${p.price_per_seat}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
