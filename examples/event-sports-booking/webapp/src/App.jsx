import React from "react";
import { Routes, Route } from "react-router-dom";
import Header from "./Header";
import Discovery from "./pages/Discovery";
import SeatSelection from "./pages/SeatSelection";
import Addons from "./pages/Addons";
import Summary from "./pages/Summary";

export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Discovery />} />
        <Route path="/seat-selection" element={<SeatSelection />} />
        <Route path="/addons" element={<Addons />} />
        <Route path="/summary" element={<Summary />} />
      </Routes>
    </>
  );
}
