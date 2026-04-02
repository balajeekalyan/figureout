import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCart } from "../CartContext";
import { askAddons } from "../api";
import "../App.css";
import "./Addons.css";

const CATEGORY_LABELS = {
  access: "Access",
  food: "Food",
  beverage: "Beverages",
  merch: "Merchandise",
  insurance: "Insurance",
};

function parsePrice(priceStr) {
  if (typeof priceStr === "number") return priceStr;
  const cleaned = String(priceStr).replace(/[^0-9.]/g, "");
  return parseFloat(cleaned) || 0;
}

export default function Addons() {
  const navigate = useNavigate();
  const { setAddons } = useCart();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [selected, setSelected] = useState([]);
  const [addons, setAddonsList] = useState([]);

  const toggleAddon = (addon) => {
    const price = parsePrice(addon.price);
    setSelected((prev) =>
      prev.find((a) => a.name === addon.name)
        ? prev.filter((a) => a.name !== addon.name)
        : [...prev, { name: addon.name, price }]
    );
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await askAddons(query);
      const payload = data.response || data;
      setAddonsList(payload.addons || []);
      setSummary(payload.summary || "");
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

  const categories = [...new Set(addons.map((a) => a.category).filter(Boolean))];
  const grouped = categories.map((cat) => ({
    category: cat,
    label: CATEGORY_LABELS[cat] || cat,
    items: addons.filter((a) => a.category === cat),
  }));

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
                      <div className="addon-row-info">
                        <span className="addon-row-name">{addon.name}</span>
                        {addon.description && (
                          <span className="addon-row-desc">{addon.description}</span>
                        )}
                      </div>
                      <span className="addon-row-price">${parsePrice(addon.price).toFixed(2)}</span>
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
