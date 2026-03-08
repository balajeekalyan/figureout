import React from "react";
import { Link } from "react-router-dom";
import "./Header.css";

export default function Header() {
  return (
    <header className="header">
      <Link to="/" className="header-title">
        Concert Booking
      </Link>
    </header>
  );
}
