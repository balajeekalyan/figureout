import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const askDiscovery = async (userQuery, date, toDate) => {
  const response = await api.post("/ask", {
    user_query: userQuery,
    role: 'flight_discovery',
    context: `fromDate: ${date}, toDate: ${toDate}`,
  });
  return response.data;
};

export const getSeats = async (flightNumber, tier) => {
  const params = tier ? { tier } : {};
  const response = await api.get(`/seats/${flightNumber}`, { params });
  return response.data;
};

export const askSeatSelection = async (userQuery, flightNumber, tier) => {
  const response = await api.post("/ask", {
    user_query: userQuery,
    role: 'seat_selection',
    context: `flightNumber: ${flightNumber}, tier: ${tier}`,
  });
  return response.data;
};

export const getAddons = async (flightNumber, tier) => {
  const params = tier ? { tier } : {};
  const response = await api.get(`/addons/${flightNumber}`, { params });
  return response.data;
};

export const askAddons = async (userQuery, flightNumber, tier) => {
  const response = await api.post("/ask", {
    user_query: userQuery,
    role: 'addons_selection',
    context: `flightNumber: ${flightNumber}, tier: ${tier}`,
  });
  return response.data;
};

export const fetchFees = async (flightNumber) => {
  const response = await api.get(`/fees/${flightNumber}`);
  return response.data;
};

export const askFees = async (userQuery, flightNumber) => {
  const response = await api.post("/ask", {
    user_query: userQuery,
    role: "explain_fees",
    context: `flight_number: ${flightNumber}`,
  });
  return response.data;
};
