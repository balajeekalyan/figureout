const BASE_URL = "http://localhost:8000";

export const askDiscovery = async (userQuery, fromDate, toDate, location) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "places_discovery",
      context: `from_date: ${fromDate}, to_date: ${toDate}, location: ${location}`,
    }),
  });
  return response.json();
};

export const askActivities = async (userQuery, placeId, fromDate, toDate) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "things_to_do_discovery",
      context: `place_id: ${placeId}, from_date: ${fromDate}, to_date: ${toDate}`,
    }),
  });
  return response.json();
};

export const fetchActivities = async (placeId, fromDate, toDate) => {
  const params = new URLSearchParams();
  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);
  const response = await fetch(`${BASE_URL}/activities/${placeId}?${params}`);
  return response.json();
};

export const fetchAddons = async (activityId) => {
  const response = await fetch(`${BASE_URL}/addons/${activityId}`);
  return response.json();
};

export const fetchFees = async (placeId) => {
  const response = await fetch(`${BASE_URL}/fees/${placeId}`);
  return response.json();
};

export const askAddons = async (userQuery, activityId) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "addons_selection",
      context: `activity_id: ${activityId}`,
    }),
  });
  return response.json();
};

export const askFees = async (userQuery, placeId) => {
  const response = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: userQuery,
      role: "explain_fees",
      context: `place_id: ${placeId}`,
    }),
  });
  return response.json();
};
