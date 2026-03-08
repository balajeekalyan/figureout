import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { fetchAddons, askAddons } from "../api";
import "../App.css";
import "./Addons.css";

const CATEGORY_LABELS = {
  experience: "Experiences",
  guide: "Guide",
  transport: "Transport",
  food: "Food & Drink",
  gear: "Gear",
};

const CATEGORY_ORDER = ["experience", "guide", "transport", "food", "gear"];

export default function Addons() {
  const navigate = useNavigate();
  const { activity, setAddons } = useCart();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [selected, setSelected] = useState([]);
  const [availableAddons, setAvailableAddons] = useState([]);

  useEffect(() => {
    if (!activity?.id) return;
    fetchAddons(activity.id)
      .then((data) => {
        const list = Array.isArray(data) ? data : (data.addons || []);
        setAvailableAddons(list);
      })
      .catch((err) => console.error("Failed to load add-ons", err));
  }, [activity?.id]);

  const toggleAddon = (addon) => {
    setSelected((prev) =>
      prev.find((a) => a.name === addon.name)
        ? prev.filter((a) => a.name !== addon.name)
        : [...prev, { name: addon.name, price: addon.price, category: addon.category }]
    );
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await askAddons(query, activity?.id);
      const payload = data.response || data;
      setSummary(payload.summary || "");
      const addonsList = Array.isArray(payload) ? payload : (payload.addons || []);
      if (addonsList.length > 0) {
        setAvailableAddons(addonsList);
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

  const grouped = CATEGORY_ORDER
    .map((cat) => ({
      category: cat,
      label: CATEGORY_LABELS[cat] || cat,
      items: availableAddons.filter((a) => a.category === cat),
    }))
    .filter((g) => g.items.length > 0);

  return (
    <div className="app">
      <h2>Add-ons</h2>

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
                    className={`addon-row${isSelected ? " addon-row--selected" : ""}`}
                    onClick={() => toggleAddon(addon)}
                  >
                    <span className="addon-row-name">{addon.name}</span>
                    <span className="addon-row-price">${addon.price.toFixed(2)}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      <button
        onClick={() => {
          setAddons(selected);
          navigate("/summary");
        }}
        className="continue-btn"
      >
        Continue to Summary
        {selected.length > 0 &&
          ` (${selected.length} add-on${selected.length !== 1 ? "s" : ""})`}
      </button>
    </div>
  );
}
