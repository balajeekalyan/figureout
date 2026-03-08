import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { getAddons, askAddons } from "../api";
import "../App.css";
import "./Addons.css";

const CATEGORY_LABELS = {
  luggage: "Luggage",
  insurance: "Insurance",
  food: "Food",
  beverage: "Beverages",
  alcoholic_beverage: "Alcoholic Beverages",
};

const CATEGORY_ORDER = ["luggage", "insurance", "food", "beverage", "alcoholic_beverage"];

export default function Addons() {
  const navigate = useNavigate();
  const { flight, setAddons } = useCart();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [availableAddons, setAvailableAddons] = useState([]);
  const [selected, setSelected] = useState([]);

  const flightNumber = flight?.flight_number || "";
  const tier = flight?.tier || "";

  useEffect(() => {
    if (!flightNumber) return;
    const fetchAddons = async () => {
      try {
        const data = await getAddons(flightNumber, tier);
        if (Array.isArray(data)) {
          setAvailableAddons(data);
          const included = data.filter((a) => a.included);
          setSelected(included.map((a) => ({ name: a.name, price: a.price })));
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchAddons();
  }, [flightNumber, tier]);

  const toggleAddon = (addon) => {
    if (addon.included) return;
    setSelected((prev) =>
      prev.find((a) => a.name === addon.name)
        ? prev.filter((a) => a.name !== addon.name)
        : [...prev, { name: addon.name, price: addon.price }]
    );
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await askAddons(query, flightNumber, tier);
      const res = data?.response || data;
      setSummary(res?.summary || "");
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

  const grouped = CATEGORY_ORDER
    .map((cat) => ({
      category: cat,
      label: CATEGORY_LABELS[cat] || cat,
      items: availableAddons.filter((a) => a.category === cat),
    }))
    .filter((g) => g.items.length > 0);

  const paidSelected = selected.filter((a) => a.price > 0);

  return (
    <div className="app">
      <h2>Add-ons</h2>
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
          placeholder="Ask about add-ons..."
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {summary && <p className="summary">{summary}</p>}

      <div className="addons-sections">
        {grouped.map((group) => (
          <div key={group.category} className="addons-category">
            <h3 className="addons-category-title">{group.label}</h3>
            <ul className="addons-list">
              {group.items.map((addon) => {
                const isSelected = !!selected.find((a) => a.name === addon.name);
                return (
                  <li
                    key={addon.name}
                    className={`addon-row${isSelected ? " addon-row--selected" : ""}${addon.included ? " addon-row--included" : ""}`}
                    onClick={() => toggleAddon(addon)}
                  >
                    <span className="addon-row-name">{addon.name}</span>
                    <span className="addon-row-price">
                      {addon.included ? "Included" : `$${addon.price}`}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      <button
        onClick={() => {
          setAddons(paidSelected);
          navigate("/summary");
        }}
        className="continue-btn"
      >
        Continue to Summary
        {paidSelected.length > 0 &&
          ` (${paidSelected.length} add-on${paidSelected.length !== 1 ? "s" : ""})`}
      </button>
    </div>
  );
}
