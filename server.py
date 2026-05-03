import json
import asyncio
import logging
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

mcp = FastMCP("scryfall")

SCRYFALL = "https://api.scryfall.com"
HEADERS = {"User-Agent": "MTG-MCP/1.0", "Accept": "application/json"}
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 0.1


async def scryfall_get(client: httpx.AsyncClient, path: str) -> dict:
    """Fetch from Scryfall with automatic retry on rate limits."""
    url = path if path.startswith("http") else f"{SCRYFALL}{path}"
    await asyncio.sleep(RATE_LIMIT_DELAY)
    for attempt in range(MAX_RETRIES):
        log.info("GET %s (attempt %d)", url, attempt + 1)
        r = await client.get(url, headers=HEADERS)
        log.info("← %d", r.status_code)
        if r.status_code == 429:
            wait = float(r.headers.get("Retry-After", 1))
            log.warning("Rate limited; waiting %.1fs", wait)
            await asyncio.sleep(wait)
            continue
        if r.status_code != 200:
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            raise Exception(body.get("details") or f"Scryfall API error {r.status_code}")
        return r.json()
    raise Exception("Rate limited by Scryfall after retries")


def image_uri(card: dict) -> str | None:
    if uris := card.get("image_uris"):
        return uris.get("normal")
    if faces := card.get("card_faces"):
        return (faces[0].get("image_uris") or {}).get("normal")
    return None


def image_uris_all(card: dict) -> dict | None:
    """Get all image URIs (small, normal, large, art_crop, etc.)."""
    if uris := card.get("image_uris"):
        return uris
    if faces := card.get("card_faces"):
        result = {}
        for i, face in enumerate(faces):
            prefix = f"face{i + 1}_"
            for k, v in (face.get("image_uris") or {}).items():
                result[f"{prefix}{k}"] = v
        return result if result else None
    return None


def extract_prices(card: dict) -> dict:
    return {k: v for k, v in (card.get("prices") or {}).items() if v is not None}


def card_data(card: dict) -> dict:
    """Extract comprehensive card data from a Scryfall card object."""
    faces = card.get("card_faces") or []

    def from_faces(key):
        return "\n// ---\n".join(f[key] for f in faces if f.get(key))

    result = {
        "name": card["name"],
        "layout": card.get("layout"),
        "type_line": card.get("type_line") or from_faces("type_line") or None,
        "mana_cost": card.get("mana_cost") or from_faces("mana_cost") or None,
        "cmc": card.get("cmc"),
        "oracle_text": card.get("oracle_text") or from_faces("oracle_text") or None,
        "flavor_text": card.get("flavor_text") or from_faces("flavor_text") or None,
        "keywords": card.get("keywords", []),
        "colors": card.get("colors") or (faces[0].get("colors") if faces else []),
        "color_identity": card.get("color_identity", []),
        "power": card.get("power") or (faces[0].get("power") if faces else None),
        "toughness": card.get("toughness") or (faces[0].get("toughness") if faces else None),
        "loyalty": card.get("loyalty") or (faces[0].get("loyalty") if faces else None),
        "defense": card.get("defense"),
        "produced_mana": card.get("produced_mana"),
        "prices": extract_prices(card),
        "set": card.get("set_name") or card.get("set"),
        "set_code": card.get("set"),
        "rarity": card.get("rarity"),
        "collector_number": card.get("collector_number"),
        "artist": card.get("artist"),
        "edhrec_rank": card.get("edhrec_rank"),
        "penny_rank": card.get("penny_rank"),
        "legalities": card.get("legalities", {}),
        "games": card.get("games", []),
        "image_uris": image_uris_all(card),
        "scryfall_uri": card.get("scryfall_uri"),
    }

    # Include related cards (tokens, meld pieces, combo parts)
    if all_parts := card.get("all_parts"):
        result["related_cards"] = [
            {"name": p.get("name"), "type_line": p.get("type_line"), "component": p.get("component")}
            for p in all_parts
        ]

    # Include related URIs (EDHREC, Gatherer, etc.)
    if related := card.get("related_uris"):
        result["related_uris"] = related

    return result


def card_summary(card: dict) -> dict:
    """Extract a rich summary for search results — enough for the AI to reason about."""
    faces = card.get("card_faces") or []

    def from_faces(key):
        return " // ".join(f[key] for f in faces if f.get(key))

    return {
        "name": card["name"],
        "type_line": card.get("type_line") or from_faces("type_line") or None,
        "mana_cost": card.get("mana_cost") or from_faces("mana_cost") or None,
        "cmc": card.get("cmc"),
        "oracle_text": card.get("oracle_text") or from_faces("oracle_text") or None,
        "colors": card.get("colors") or (faces[0].get("colors") if faces else []),
        "color_identity": card.get("color_identity", []),
        "keywords": card.get("keywords", []),
        "power": card.get("power") or (faces[0].get("power") if faces else None),
        "toughness": card.get("toughness") or (faces[0].get("toughness") if faces else None),
        "loyalty": card.get("loyalty") or (faces[0].get("loyalty") if faces else None),
        "rarity": card.get("rarity"),
        "price_usd": (card.get("prices") or {}).get("usd"),
        "price_foil": (card.get("prices") or {}).get("usd_foil"),
        "set": card.get("set_name") or card.get("set"),
        "edhrec_rank": card.get("edhrec_rank"),
        "legalities": card.get("legalities", {}),
        "scryfall_uri": card.get("scryfall_uri"),
        "image_uri": image_uri(card),
    }


@mcp.tool()
async def search_cards(query: str, limit: int = 20) -> str:
    """Search for Magic: The Gathering cards using Scryfall search syntax.

    Args:
        query: Scryfall search query (e.g. "t:dragon id<=ur mv<=5")
        limit: Max results to return (default 20, max 175)
    """
    limit = min(max(limit, 1), 175)
    cards = []
    encoded_query = quote(query, safe="")
    url = f"/cards/search?q={encoded_query}"

    async with httpx.AsyncClient() as client:
        while url and len(cards) < limit:
            data = await scryfall_get(client, url)
            for c in data["data"]:
                if len(cards) >= limit:
                    break
                cards.append(card_summary(c))
            url = data.get("next_page") if data.get("has_more") else None
            if url:
                await asyncio.sleep(RATE_LIMIT_DELAY)

    return json.dumps(cards, indent=2, default=str)


@mcp.tool()
async def get_card_data(card_names: list[str]) -> str:
    """Fetch comprehensive data for specific Magic: The Gathering cards by name.

    Args:
        card_names: List of card names to look up
    """
    if len(card_names) > 20:
        return json.dumps({"error": "Maximum 20 cards per request"})

    results = []
    errors = []

    async with httpx.AsyncClient() as client:
        for i, name in enumerate(card_names):
            try:
                card = await scryfall_get(client, f"/cards/named?fuzzy={quote(name, safe='')}")
                results.append(card_data(card))
            except Exception as e:
                errors.append(f"{name}: {e}")
            if i < len(card_names) - 1:
                await asyncio.sleep(RATE_LIMIT_DELAY)

    output = {"cards": results}
    if errors:
        output["errors"] = errors
    return json.dumps(output, indent=2, default=str)


@mcp.tool()
async def get_rulings(card_name: str) -> str:
    """Get official rulings for a Magic: The Gathering card.

    Args:
        card_name: Card name to get rulings for
    """
    async with httpx.AsyncClient() as client:
        card = await scryfall_get(client, f"/cards/named?fuzzy={quote(card_name, safe='')}")
        await asyncio.sleep(RATE_LIMIT_DELAY)
        rulings = await scryfall_get(client, f"/cards/{card['id']}/rulings")

    result = [
        {"date": r.get("published_at"), "text": r.get("comment"), "source": r.get("source")}
        for r in rulings["data"]
    ]
    if not result:
        return f'No rulings found for "{card["name"]}".'
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
async def download_image(card_name: str) -> str:
    """Download a Magic: The Gathering card image to the local MagicCards folder.

    Args:
        card_name: Card name to download image for
    """
    async with httpx.AsyncClient() as client:
        card = await scryfall_get(client, f"/cards/named?fuzzy={quote(card_name, safe='')}")

        url = (
            (card.get("image_uris") or {}).get("large")
            or (card.get("image_uris") or {}).get("normal")
            or ((card.get("card_faces") or [{}])[0].get("image_uris") or {}).get("large")
            or ((card.get("card_faces") or [{}])[0].get("image_uris") or {}).get("normal")
        )
        if not url:
            raise Exception(f'No image available for "{card["name"]}".')

        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()

    folder = Path("MagicCards")
    folder.mkdir(exist_ok=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", unicodedata.normalize("NFC", card["name"]))
    ext = "png" if ".png" in url else "jpg"
    path = folder / f"{safe_name}.{ext}"
    path.write_bytes(r.content)

    return json.dumps({
        "status": "success",
        "card_name": card["name"],
        "file_path": str(path.resolve()),
        "size_bytes": len(r.content),
    }, indent=2, default=str)


@mcp.tool()
async def get_random_card(query: str | None = None) -> str:
    """Get a random Magic: The Gathering card, optionally filtered by a Scryfall query.

    Args:
        query: Optional Scryfall search query to filter random results (e.g. "t:legendary id=wubrg")
    """
    path = "/cards/random"
    if query:
        path += f"?q={quote(query, safe='')}"

    async with httpx.AsyncClient() as client:
        card = await scryfall_get(client, path)

    return json.dumps(card_data(card), indent=2, default=str)


@mcp.tool()
async def autocomplete_card_name(partial: str) -> str:
    """Autocomplete a partial Magic: The Gathering card name. Returns up to 20 suggestions.

    Args:
        partial: Partial card name to autocomplete (e.g. "Thalia" or "Black Lo")
    """
    async with httpx.AsyncClient() as client:
        data = await scryfall_get(client, f"/cards/autocomplete?q={quote(partial, safe='')}")

    return json.dumps(data.get("data", []), indent=2, default=str)


@mcp.tool()
async def get_set_info(set_code: str) -> str:
    """Get information about a Magic: The Gathering set by its code.

    Args:
        set_code: The set code (e.g. "mh3" for Modern Horizons 3, "dsk" for Duskmourn)
    """
    async with httpx.AsyncClient() as client:
        data = await scryfall_get(client, f"/sets/{quote(set_code.lower(), safe='')}")

    return json.dumps({
        "name": data.get("name"),
        "code": data.get("code"),
        "set_type": data.get("set_type"),
        "released_at": data.get("released_at"),
        "card_count": data.get("card_count"),
        "digital": data.get("digital"),
        "icon_svg_uri": data.get("icon_svg_uri"),
        "scryfall_uri": data.get("search_uri"),
        "parent_set_code": data.get("parent_set_code"),
        "block": data.get("block"),
        "block_code": data.get("block_code"),
    }, indent=2, default=str)


@mcp.tool()
async def get_card_prints(card_name: str) -> str:
    """Get all printings/versions of a Magic: The Gathering card across all sets.

    Args:
        card_name: Card name to look up printings for
    """
    async with httpx.AsyncClient() as client:
        card = await scryfall_get(client, f"/cards/named?fuzzy={quote(card_name, safe='')}")

        prints_uri = card.get("prints_search_uri")
        if not prints_uri:
            return json.dumps({"error": f'No print history available for "{card["name"]}" (may be a token or emblem)'})

        all_prints = []
        url = prints_uri
        while url:
            data = await scryfall_get(client, url)
            for p in data["data"]:
                all_prints.append({
                    "name": p["name"],
                    "set": p.get("set_name") or p.get("set"),
                    "set_code": p.get("set"),
                    "collector_number": p.get("collector_number"),
                    "rarity": p.get("rarity"),
                    "released_at": p.get("released_at"),
                    "price_usd": (p.get("prices") or {}).get("usd"),
                    "price_foil": (p.get("prices") or {}).get("usd_foil"),
                    "artist": p.get("artist"),
                    "digital": p.get("digital", False),
                    "image_uri": image_uri(p),
                    "scryfall_uri": p.get("scryfall_uri"),
                })
            url = data.get("next_page") if data.get("has_more") else None
            if url:
                await asyncio.sleep(RATE_LIMIT_DELAY)

    return json.dumps({
        "card_name": card["name"],
        "total_prints": len(all_prints),
        "prints": all_prints,
    }, indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
