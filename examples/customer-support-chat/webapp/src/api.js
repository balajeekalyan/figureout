const BASE_URL = "http://localhost:8000";

export const sendMessage = async (userQuery) => {
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_query: userQuery }),
  });
  return response.json();
};
