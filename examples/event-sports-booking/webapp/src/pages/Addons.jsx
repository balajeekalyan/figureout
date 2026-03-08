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

const CATEGORY_ORDER = ["access", "food", "beverage", "merch", "insurance"];

const AVAILABLE_ADDONS = [
  { name: "VIP Lounge Access", category: "access", price: 75 },
  { name: "Parking Pass", category: "access", price: 25 },
  { name: "Meet & Greet", category: "access", price: 120 },
  { name: "Cheeseburger", category: "food", price: 12 },
  { name: "Cheese Platter", category: "food", price: 14 },
  { name: "Chicken Wrap", category: "food", price: 11 },
  { name: "Fresh Fruit Bowl", category: "food", price: 9 },
  { name: "Cookie Pack", category: "food", price: 5 },
  { name: "Coffee", category: "beverage", price: 4 },
  { name: "Orange Juice", category: "beverage", price: 5 },
  { name: "Sparkling Water", category: "beverage", price: 3 },
  { name: "Red Wine", category: "beverage", price: 10 },
  { name: "Beer", category: "beverage", price: 8 },
  { name: "Whiskey", category: "beverage", price: 12 },
  { name: "Event T-Shirt", category: "merch", price: 35 },
  { name: "Poster", category: "merch", price: 15 },
  { name: "Tote Bag", category: "merch", price: 20 },
  { name: "Event Insurance", category: "insurance", price: 18 },
];

export default function Addons() {
  const navigate = useNavigate();
  const { setAddons } = useCart();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [selected, setSelected] = useState([]);

  const toggleAddon = (addon) => {
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
      const data = await askAddons(query);
      setSummary(data.summary || "");
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
      items: AVAILABLE_ADDONS.filter((a) => a.category === cat),
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
                    <span className="addon-row-price">${addon.price}</span>
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
