import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

chat_mcp = FastMCP("Customer Support Chat MCP")

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        with open(path) as f:
            return json.load(f)
    return []


def _search(faqs: list, query: str) -> list:
    """Return FAQ articles matching the query by tag or question text.
    Falls back to all articles if nothing matches."""
    query_lower = query.lower()
    results = [
        f for f in faqs
        if any(tag in query_lower for tag in f.get("tags", []))
        or query_lower in f["question"].lower()
        or query_lower in f["answer"].lower()
    ]
    return results if results else faqs


@chat_mcp.tool(
    name="search_account_faq",
    description="Search the account management FAQ for information about passwords, login, profile settings, email changes, two-factor authentication, and account deletion.",
)
async def search_account_faq(query: str) -> str:
    """Search account management FAQ articles relevant to the user's query."""
    faqs = load_json("account_faq.json")
    return json.dumps(_search(faqs, query))


@chat_mcp.tool(
    name="search_billing_faq",
    description="Search the billing FAQ for information about payment methods, invoices, refunds, subscriptions, failed payments, promo codes, and taxes.",
)
async def search_billing_faq(query: str) -> str:
    """Search billing FAQ articles relevant to the user's query."""
    faqs = load_json("billing_faq.json")
    return json.dumps(_search(faqs, query))


@chat_mcp.tool(
    name="search_order_faq",
    description="Search the order FAQ for information about order tracking, cancellations, returns, delivery times, missing items, and wrong items received.",
)
async def search_order_faq(query: str) -> str:
    """Search order FAQ articles relevant to the user's query."""
    faqs = load_json("order_faq.json")
    return json.dumps(_search(faqs, query))


if __name__ == "__main__":
    chat_mcp.run()
