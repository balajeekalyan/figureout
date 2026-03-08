import React, { createContext, useContext, useState } from "react";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [flight, setFlight] = useState(null);
  const [seats, setSeats] = useState([]);
  const [addons, setAddons] = useState([]);

  const resetCart = () => {
    setFlight(null);
    setSeats([]);
    setAddons([]);
  };

  return (
    <CartContext.Provider
      value={{ flight, setFlight, seats, setSeats, addons, setAddons, resetCart }}
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
