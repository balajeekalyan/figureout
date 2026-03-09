import React from "react";
import "./PlacesResults.css";

export default function PlacesResults({ places, onExplore }) {
  if (!places || places.length === 0) return null;

  return (
    <div className="places-results">
      {places.map((place, index) => (
        <div className="place-card" key={place.id || index}>
          <div className="place-card-header">
            <div>
              <h3 className="place-card-name">{place.name}</h3>
              <span className="place-card-country">{place.country}</span>
            </div>
            <button
              className="place-explore-btn"
              onClick={() => onExplore(place)}
            >
              Explore
            </button>
          </div>
          {place.description && (
            <p className="place-card-description">{place.description}</p>
          )}
          {place.highlights?.length > 0 && (
            <div className="place-card-highlights">
              {place.highlights.map((h, i) => (
                <span className="place-highlight-tag" key={i}>{h}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
