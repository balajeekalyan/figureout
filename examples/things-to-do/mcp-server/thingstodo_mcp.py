import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

thingstodo_mcp = FastMCP("Things To Do MCP")

DATA_DIR = Path(__file__).parent / "data"

_COUNTRY_ALIASES = {
    "usa": "united states",
    "us": "united states",
    "u.s.a.": "united states",
    "u.s.": "united states",
    "uk": "united kingdom",
    "gb": "united kingdom",
}


def _normalize_location(loc: str) -> str:
    """Expand known abbreviations to their full country name."""
    return _COUNTRY_ALIASES.get(loc, loc)


def matches_location(location: str, city: str, country: str) -> bool:
    """Check if location matches city or country using flexible matching."""
    loc = _normalize_location(location.lower().strip())
    city_lower = city.lower().strip()
    country_lower = _normalize_location(country.lower().strip())
    if loc in city_lower or city_lower in loc:
        return True
    if loc in country_lower or country_lower in loc:
        return True
    city_parts = [p.strip() for p in city.split(",")]
    for part in city_parts:
        part_lower = part.lower()
        if loc in part_lower or part_lower in loc:
            return True
    return False


def matches_date(date: str, from_date: str, to_date: str) -> bool:
    """Check if a date falls within the from_date and to_date range (YYYY-MM-DD)."""
    return from_date <= date <= to_date


def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        with open(path) as f:
            return json.load(f)
    return []


@thingstodo_mcp.tool(name="get_places", description="Search places (cities) by name or country. Returns matching destinations with highlights and descriptions.")
async def get_places(query: str, country: str = "") -> str:
    """Get places matching a city name query or country filter."""
    places = load_json("places.json")
    results = []
    for p in places:
        name_match = query.lower() in p["name"].lower() or p["name"].lower() in query.lower()
        country_match = not country or matches_location(country, p["name"], p["country"])
        if name_match or country_match:
            results.append(p)
    if results:
        return json.dumps(results)
    # Fall back: return all places if no specific match
    return json.dumps(places)


@thingstodo_mcp.tool(name="get_activities_by_place", description="Get all activities available at a specific place by place_id. Requires from_date (YYYY-MM-DD) and to_date (YYYY-MM-DD) from user context.")
async def get_activities_by_place(place_id: int, from_date: str, to_date: str) -> str:
    """Get all activities at a given place filtered by date range."""
    activities = load_json("thingstodo.json")
    results = []
    for a in activities:
        if a["place_id"] != place_id:
            continue
        filtered_details = [
            d for d in a["details"]
            if matches_date(d["date"], from_date, to_date)
        ]
        if filtered_details:
            results.append({**a, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No activities found for place_id {place_id} between {from_date} and {to_date}"})


@thingstodo_mcp.tool(name="get_activities_by_type", description="Search activities by type (Sightseeing, Adventure, Cultural, Food & Drink, Nature, Workshop) filtered by city and date range. Requires from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and city from user context.")
async def get_activities_by_type(type: str, city: str, from_date: str, to_date: str) -> str:
    """Get activities matching a type filtered by city and date range."""
    activities = load_json("thingstodo.json")
    results = []
    for a in activities:
        if type.lower() not in a["type"].lower():
            continue
        if not matches_location(city, a["city"], a["country"]):
            continue
        filtered_details = [
            d for d in a["details"]
            if matches_date(d["date"], from_date, to_date)
        ]
        if filtered_details:
            results.append({**a, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No '{type}' activities found in '{city}'"})


@thingstodo_mcp.tool(name="search_activities", description="Search activities by keyword across name and description, filtered by city and date range. Requires from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and city from user context.")
async def search_activities(keyword: str, city: str, from_date: str, to_date: str) -> str:
    """Keyword search across activity names and descriptions filtered by city and date range."""
    activities = load_json("thingstodo.json")
    results = []
    kw = keyword.lower()
    for a in activities:
        text = (a["name"] + " " + a["description"]).lower()
        if kw not in text:
            continue
        if not matches_location(city, a["city"], a["country"]):
            continue
        filtered_details = [
            d for d in a["details"]
            if matches_date(d["date"], from_date, to_date)
        ]
        if filtered_details:
            results.append({**a, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No activities matching '{keyword}' found in '{city}'"})


@thingstodo_mcp.tool(name="get_addons", description="Get all available add-ons for a specific activity by its activity_id.")
async def get_addons(activity_id: int) -> str:
    """Get all add-ons available for the given activity_id."""
    addons = load_json("addons.json")
    results = [a for a in addons if a["activity_id"] == activity_id]
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No add-ons found for activity_id {activity_id}"})


@thingstodo_mcp.tool(name="get_fees", description="Get all applicable fees for a specific place by its place_id. Fees include service fee, convenience fee, tourism levy, and local tax with descriptions of how each is calculated.")
async def get_fees(place_id: int) -> str:
    """Get all fees applicable to the given place_id."""
    fees = load_json("fees.json")
    result = next((f for f in fees if f["place_id"] == place_id), None)
    if result:
        return json.dumps(result)
    return json.dumps({"error": f"No fees found for place_id {place_id}"})


if __name__ == "__main__":
    thingstodo_mcp.run()
