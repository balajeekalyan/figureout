import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

flight_mcp = FastMCP("Flight Booking")

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        with open(path) as f:
            return json.load(f)
    return []

flights = load_json("flight.json")
seats = load_json("seats.json")
addons = load_json("addons.json")


def to_str(value) -> str | None:
    """Coerce a value to a stripped string, or None if empty/invalid."""
    if value is None:
        return None
    if isinstance(value, dict):
        value = next(iter(value.values()), None) if value else None
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def filter_routes_by_date(routes: list, from_date: str = None, to_date: str = None) -> list:
    """Filter routes by departure date range. Dates should be YYYY-MM-DD."""
    from_date = to_str(from_date)
    to_date = to_str(to_date)
    if not from_date and not to_date:
        return routes
    return [
        r for r in routes
        if (not from_date or r["source_depart_date"] >= from_date)
        and (not to_date or r["source_depart_date"] <= to_date)
    ]


@flight_mcp.tool(name="lookup_by_carrier", description="Look up flights by carrier/airline name, optionally filtered by a date range (YYYY-MM-DD)")
async def lookup_by_carrier(carrier_name: str, from_date: str = None, to_date: str = None) -> str:
    """Look up all routes for a given carrier/airline. Matches partial, case-insensitive names. Optionally filter by from_date and/or to_date."""
    carrier_name = to_str(carrier_name)
    if not carrier_name:
        return json.dumps({"error": "carrier_name parameter is required"})
    results = []
    for carrier in flights:
        if carrier_name.lower() in carrier["carrier_name"].lower():
            filtered = filter_routes_by_date(carrier["routes"], from_date, to_date)
            if filtered:
                results.append({
                    "id": carrier["id"],
                    "carrier_name": carrier["carrier_name"],
                    "routes": filtered,
                })
    if not results:
        return json.dumps({"error": f"No carrier matching '{carrier_name}' found"})
    return json.dumps(results)


@flight_mcp.tool(name="lookup_by_city", description="Look up flights by source or destination city, optionally filtered by a date range (YYYY-MM-DD)")
async def lookup_by_city(city: str, from_date: str = None, to_date: str = None) -> str:
    """Look up flights that depart from or arrive at a given city. Matches partial, case-insensitive city names. Optionally filter by from_date and/or to_date."""
    city = to_str(city)
    if not city:
        return json.dumps({"error": "city parameter is required"})
    results = []
    for carrier in flights:
        matching_routes = [
            r for r in carrier["routes"]
            if city.lower() in r["source_city"].lower()
            or city.lower() in r["destination_city"].lower()
        ]
        filtered = filter_routes_by_date(matching_routes, from_date, to_date)
        if filtered:
            results.append({
                "carrier_name": carrier["carrier_name"],
                "routes": filtered,
            })
    if not results:
        return json.dumps({"error": f"No flights found for city '{city}'"})
    return json.dumps(results)


@flight_mcp.tool(name="lookup_by_time_range", description="Look up flights departing within a date/time range")
async def lookup_by_time_range(from_date: str = None, to_date: str = None, start_time: str = None, end_time: str = None) -> str:
    """Look up flights within a date and/or time range. Dates should be YYYY-MM-DD, times should be HH:MM (24h)."""
    start_time = to_str(start_time)
    end_time = to_str(end_time)
    results = []
    for carrier in flights:
        date_filtered = filter_routes_by_date(carrier["routes"], from_date, to_date)
        matching_routes = [
            r for r in date_filtered
            if (not start_time or r["source_depart_time"] >= start_time)
            and (not end_time or r["source_depart_time"] <= end_time)
        ]
        if matching_routes:
            results.append({
                "carrier_name": carrier["carrier_name"],
                "routes": matching_routes,
            })
    if not results:
        return json.dumps({"error": "No flights found in the specified range"})
    return json.dumps(results)


@flight_mcp.tool(name="get_seats", description="Get available seats for a flight, optionally filtered by tier")
async def get_seats(flight_number: str, tier: str = None) -> str:
    """Get seats for a given flight number. Optionally filter by tier (Economy, First Class, Business)."""
    flight_seats = next((s for s in seats if s["flight_number"].upper() == flight_number.upper()), None)
    if not flight_seats:
        return json.dumps({"error": f"No seats found for flight '{flight_number}'"})
    rows = flight_seats["section"]["rows"]
    if tier:
        rows = [r for r in rows if r["tier"].lower() == tier.lower()]
    if not rows:
        return json.dumps({"error": f"No seats found for tier '{tier}' on flight '{flight_number}'"})
    return json.dumps({
        "flight_number": flight_seats["flight_number"],
        "section": {
            "id": flight_seats["section"]["id"],
            "rows": rows,
        },
    })


@flight_mcp.tool(name="get_addons", description="Get available add-ons for a flight, optionally filtered by tier")
async def get_addons(flight_number: str, tier: str = None) -> str:
    """Get add-ons for a given flight number. Optionally filter by tier (Economy, First Class, Business)."""
    flight_number = to_str(flight_number)
    if not flight_number:
        return json.dumps({"error": "flight_number parameter is required"})
    tier = to_str(tier)
    results = [
        a for a in addons
        if a["flight_number"].upper() == flight_number.upper()
    ]
    if not results:
        return json.dumps({"error": f"No add-ons found for flight '{flight_number}'"})
    if tier:
        results = [a for a in results if a["tier"].lower() == tier.lower()]
    if not results:
        return json.dumps({"error": f"No add-ons found for tier '{tier}' on flight '{flight_number}'"})
    return json.dumps(results)


@flight_mcp.tool(name="get_fees", description="Get all applicable fees for a specific flight by its flight number. Fees include service fee, convenience fee, fuel surcharge, and sales tax with descriptions of how each is calculated.")
async def get_fees(flight_number: str) -> str:
    """Get all fees applicable to the given flight_number."""
    flight_number = to_str(flight_number)
    if not flight_number:
        return json.dumps({"error": "flight_number parameter is required"})
    fees = load_json("fees.json")
    result = next((f for f in fees if f["flight_number"].upper() == flight_number.upper()), None)
    if result:
        return json.dumps(result)
    return json.dumps({"error": f"No fees found for flight_number {flight_number}"})


@flight_mcp.resource("flight://{flight_number}/seats")
async def get_flight_seats(flight_number: str) -> str:
    """Get all seats for a flight by flight number."""
    flight_seats = next((s for s in seats if s["flight_number"].upper() == flight_number.upper()), None)
    if not flight_seats:
        return json.dumps({"error": f"No seats found for flight '{flight_number}'"})
    return json.dumps(flight_seats)

