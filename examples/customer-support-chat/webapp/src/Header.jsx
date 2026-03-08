import React from "react";
import { Link } from "react-router-dom";
import "./Header.css";

export default function Header() {
  return (
    <header className="header">
      <Link to="/" className="header-title">
        Customer Support
      </Link>
      <span className="header-subtitle">How can we help you today?</span>
    </header>
  );
}
