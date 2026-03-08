import React from "react";
import { Routes, Route } from "react-router-dom";
import Header from "./Header";
import Chat from "./pages/Chat";

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Chat />} />
      </Routes>
    </>
  );
}
