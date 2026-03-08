import React, { createContext, useContext, useState } from "react";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [place, setPlace] = useState(null);
  const [activity, setActivity] = useState(null);
  const [booking, setBooking] = useState(null);
  const [addons, setAddons] = useState([]);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const resetCart = () => {
    setPlace(null);
    setActivity(null);
    setBooking(null);
    setAddons([]);
    setFromDate("");
    setToDate("");
  };

  return (
    <CartContext.Provider
      value={{ place, setPlace, activity, setActivity, booking, setBooking, addons, setAddons, fromDate, setFromDate, toDate, setToDate, resetCart }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
