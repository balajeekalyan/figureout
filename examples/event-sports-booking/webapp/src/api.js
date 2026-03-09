const BASE_URL = "http://localhost:8000";

export const askDiscovery = async (userQuery, fromDate, toDate, location) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      context: `fromDate: ${fromDate}, toDate: ${toDate}, location: ${location}`,
    }),
  });
  return response.json();
};

export const getSeats = async (eventId, tier) => {
  const params = tier ? `?tier=${encodeURIComponent(tier)}` : "";
  const response = await fetch(`${BASE_URL}/seats/${eventId}${params}`);
  return response.json();
};

export const askSeatSelection = async (userQuery, eventId) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "seat_selection",
      context: `event_id: ${eventId}. Venue sections: Front (tier=Front, rows FA-FC, cols 1-12) = premium seats closest to the stage; Middle (tier=Middle, rows MA-MD, cols 1-14) = mid-range seats with good views; Back (tier=Back, rows BA-BD, cols 1-16) = budget seats furthest from the stage.`,
    }),
  });
  return response.json();
};

export const askAddons = async (userQuery) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "addons_selection",
    }),
  });
  return response.json();
};

export const fetchFees = async (eventId) => {
  const response = await fetch(`${BASE_URL}/fees/${eventId}`);
  return response.json();
};

export const askFees = async (userQuery, eventId) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "explain_fees",
      context: `event_id: ${eventId}`,
    }),
  });
  return response.json();
};
