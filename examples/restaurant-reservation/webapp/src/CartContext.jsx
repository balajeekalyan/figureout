import React, { createContext, useContext, useState } from "react";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [reservation, setReservation] = useState(null);
  const [addons, setAddons] = useState([]);

  const resetCart = () => {
    setReservation(null);
    setAddons([]);
  };

  return (
    <CartContext.Provider
      value={{ reservation, setReservation, addons, setAddons, resetCart }}
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
