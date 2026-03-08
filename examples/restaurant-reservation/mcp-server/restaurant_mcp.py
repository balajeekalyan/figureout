import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

restaurant_mcp = FastMCP("Restaurant MCP")

DATA_DIR = Path(__file__).parent / "data"

def matches_location(location: str, city: str, country: str) -> bool:
    """Check if location matches city or country using flexible matching."""
    loc = location.lower().strip()
    city_lower = city.lower().strip()
    country_lower = country.lower().strip()
    # Direct substring match in either direction
    if loc in city_lower or city_lower in loc:
        return True
    if loc in country_lower or country_lower in loc:
        return True
    # Match against city parts split by comma (e.g. "New York, NY" -> ["New York", "NY"])
    city_parts = [p.strip() for p in city.split(",")]
    for part in city_parts:
        part_lower = part.lower()
        if loc in part_lower or part_lower in loc:
            return True
    return False

def matches_date(date: str, from_date: str, to_date: str) -> bool:
    """Check if a date falls within the from_date and to_date range (YYYY-MM-DD)."""
    if not from_date and not to_date:
        return True
    if not from_date:
        return date <= to_date
    if not to_date:
        return from_date <= date
    return from_date <= date <= to_date

def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        with open(path) as f:
            return json.load(f)
    return []

@restaurant_mcp.tool(name="get_restaurants_by_cuisine", description="Search restaurants database by cuisine type. Requires from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and location from user context.")
async def get_restaurants_by_cuisine(cuisine: str, from_date: str, to_date: str, location: str) -> str:
    """Get restaurants matching a cuisine type filtered by date range and location. Use from_date, to_date, and location from the user context."""
    restaurants = load_json("food.json")
    results = []
    for r in restaurants:
        if cuisine.lower() not in r["cuisine"].lower():
            continue
        filtered_details = [
            d for d in r["details"]
            if matches_date(d["date"], from_date, to_date)
            and matches_location(location, d["city"], d["country"])
        ]
        if filtered_details:
            results.append({**r, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No restaurants found for cuisine '{cuisine}' in '{location}'"})

@restaurant_mcp.tool(name="get_restaurants_by_dietary", description="Search restaurants database by dietary requirement (e.g., vegan, vegetarian, halal, gluten-free, dairy-free, nut-free, pescatarian). Requires from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and location from user context.")
async def get_restaurants_by_dietary(dietary: str, from_date: str, to_date: str, location: str) -> str:
    """Get restaurants matching a dietary requirement filtered by date range and location. Use from_date, to_date, and location from the user context."""
    restaurants = load_json("food.json")
    results = []
    for r in restaurants:
        if dietary.lower() not in [d.lower() for d in r.get("dietary_options", [])]:
            continue
        filtered_details = [
            d for d in r["details"]
            if matches_date(d["date"], from_date, to_date)
            and matches_location(location, d["city"], d["country"])
        ]
        if filtered_details:
            results.append({**r, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No restaurants found for dietary requirement '{dietary}' in '{location}'"})

@restaurant_mcp.tool(name="get_food_by_type", description="Search food database by type (e.g., Restaurant, Food Festival, Cooking Class, Tasting Experience, Culinary Event). Requires from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and location from user context.")
async def get_food_by_type(food_type: str, from_date: str, to_date: str, location: str) -> str:
    """Get food entries matching a type filtered by date range and location. Use from_date, to_date, and location from the user context."""
    restaurants = load_json("food.json")
    results = []
    for r in restaurants:
        if food_type.lower() not in r["type"].lower():
            continue
        filtered_details = [
            d for d in r["details"]
            if matches_date(d["date"], from_date, to_date)
            and matches_location(location, d["city"], d["country"])
        ]
        if filtered_details:
            results.append({**r, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No food entries found for type '{food_type}' in '{location}'"})

@restaurant_mcp.tool(name="get_fees", description="Get all applicable fees for a specific restaurant or food experience by its ID. Fees include service fee, convenience fee, tourism fee, and sales tax with descriptions of how each is calculated.")
async def get_fees(restaurant_id: int) -> str:
    """Get all fees applicable to the given restaurant_id."""
    fees = load_json("fees.json")
    result = next((f for f in fees if f["restaurant_id"] == restaurant_id), None)
    if result:
        return json.dumps(result)
    return json.dumps({"error": f"No fees found for restaurant_id {restaurant_id}"})

@restaurant_mcp.tool(name="get_addons", description="Get all available add-ons for a specific restaurant or food experience by its ID.")
async def get_addons(restaurant_id: int) -> str:
    """Get all add-ons available for the given restaurant_id."""
    addons = load_json("addons.json")
    results = [a for a in addons if a["restaurant_id"] == restaurant_id]
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No add-ons found for restaurant_id {restaurant_id}"})

@restaurant_mcp.tool(name="get_addons_by_category", description="Get add-ons for a specific restaurant filtered by category (e.g., parking, drinks, food, experience).")
async def get_addons_by_category(restaurant_id: int, category: str) -> str:
    """Get add-ons for the given restaurant_id filtered by category."""
    addons = load_json("addons.json")
    results = [a for a in addons if a["restaurant_id"] == restaurant_id and a["category"].lower() == category.lower()]
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No add-ons found for restaurant_id {restaurant_id} in category '{category}'"})

if __name__ == "__main__":
    restaurant_mcp.run()
