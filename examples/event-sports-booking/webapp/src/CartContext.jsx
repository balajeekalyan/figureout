import React, { createContext, useContext, useState } from "react";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [event, setEvent] = useState(null);
  const [seats, setSeats] = useState([]);
  const [addons, setAddons] = useState([]);

  const resetCart = () => {
    setEvent(null);
    setSeats([]);
    setAddons([]);
  };

  return (
    <CartContext.Provider
      value={{ event, setEvent, seats, setSeats, addons, setAddons, resetCart }}
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
