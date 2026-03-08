const BASE_URL = "http://localhost:8000";

export const askDiscovery = async (userQuery, fromDate, toDate, location) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "restaurant_discovery",
      context: `from_date: ${fromDate}, to_date: ${toDate}, location: ${location}`,
    }),
  });
  return response.json();
};

export const fetchAddons = async (restaurantId) => {
  const response = await fetch(`${BASE_URL}/addons/${restaurantId}`);
  return response.json();
};

export const fetchFees = async (restaurantId) => {
  const response = await fetch(`${BASE_URL}/fees/${restaurantId}`);
  return response.json();
};

export const askAddons = async (userQuery, restaurantId) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "addons_selection",
      context: `restaurant_id: ${restaurantId}`,
    }),
  });
  return response.json();
};

export const askFees = async (userQuery, restaurantId) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "explain_fees",
      context: `restaurant_id: ${restaurantId}`,
      interpret_tool_response: true
    }),
  });
  return response.json();
};
