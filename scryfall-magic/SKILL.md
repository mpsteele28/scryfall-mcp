---
name: scryfall-magic
description: >
  Fetches comprehensive data for Magic: The Gathering cards using Scryfall.
  Use when the user asks about Magic, MTG, Magic cards, Commander, EDH,
  commanders, card searches, card suggestions, card recommendations, card
  properties, format staples, card comparisons, rulings, synergies, combos,
  strategies, budget alternatives, upgrades, or wants to analyze/optimize/find
  cards for any purpose. Supports all Scryfall search syntax including color
  identity, card types, mana costs, keywords, and format legality.
---

# Scryfall Magic: The Gathering Skill

You have 8 Scryfall MCP tools. Pick the right one and write tight queries - this keeps API calls low and answers fast.

## Tools

| Tool | Use when... | Skip when... |
|---|---|---|
| `search_cards(query, limit)` | Finding cards matching criteria (type, color, cost, text, format). Returns oracle text, stats, prices, legalities, and EDHREC rank. | You already know the exact card name - use `get_card_data` instead. |
| `get_card_data(card_names)` | You need full details on specific named cards (flavor text, artist, all image sizes, related tokens, EDHREC/Gatherer links). Always batch multiple names in one call. | You're exploring what cards exist - use `search_cards` first. |
| `get_rulings(card_name)` | The user asks about rules interactions or how a card works in specific situations. | The oracle text already answers the question. |
| `download_image(card_name)` | The user explicitly wants a card image saved locally. | The user just wants to see the card - give them `scryfall_uri` or `image_uri` from search results. |
| `get_random_card(query)` | The user wants a random card or surprise pick. Accepts an optional query to constrain results. | The user wants specific or best cards - use `search_cards`. |
| `autocomplete_card_name(partial)` | The name is truly ambiguous or badly misspelled. Returns up to 20 suggestions. | You're fairly confident about the name - `get_card_data` uses fuzzy matching. |
| `get_set_info(set_code)` | The user asks about a specific set (release date, card count, type). | You need cards from a set - use `search_cards` with `s:SET_CODE`. |
| `get_card_prints(card_name)` | Showing all printings, comparing prices across sets, or finding the cheapest version of a card. | You just need the current price - `search_cards` or `get_card_data` already include prices. |

## Decision Flowchart

1. **"Find me cards that..."** → `search_cards` with combined filters + `order:edhrec`
2. **"Tell me about [card]"** → `get_card_data(["Card Name"])` (batch if multiple)
3. **"Cheapest version / all printings"** → `get_card_prints("Card Name")`
4. **"How does [card] interact with..."** → `get_rulings("Card Name")`
5. **"What set is [code]?"** → `get_set_info("code")`
6. **"Random card"** → `get_random_card(optional_query)`
7. **"Did you mean...?"** → `autocomplete_card_name("partial")`
8. **"Save the image"** → `download_image("Card Name")`

Most questions are #1 or #2. When in doubt, start with `search_cards`.

## Efficiency Rules

### 1. Search results are rich - don't follow up unnecessarily

`search_cards` returns: name, type_line, mana_cost, cmc, oracle_text, colors, color_identity, keywords, power, toughness, loyalty, rarity, prices, set, EDHREC rank, legalities, scryfall_uri, and image_uri.

Only call `get_card_data` after a search if you specifically need: flavor text, artist, all image sizes, related tokens/meld pieces, EDHREC/Gatherer links, collector number, or penny rank.

### 2. Batch card lookups into a single call

Good: `get_card_data(["Sol Ring", "Mana Crypt", "Arcane Signet"])`
Bad: Three separate `get_card_data` calls.

### 3. Write one precise query instead of multiple vague ones

Good: `search_cards("t:creature id<=bg mv<=3 o:deathtouch f:commander")` - one call.
Bad: Searching "deathtouch creatures", then "black green creatures", then merging manually.

### 4. Use `order:edhrec` for Commander recommendations

When the user asks for staples or deck suggestions, add `order:edhrec` to sort by EDHREC popularity.

Example: `search_cards("id<=wr t:enchantment f:commander order:edhrec", limit=15)`

### 5. Keep limits practical

Default is 20, max is 175. For recommendations, 10–15 is usually enough. Don't request 175 when the user asked for "a few suggestions."

## Common Task Patterns

### Deck building / card suggestions
1. `search_cards` with color identity (`id<=`), format legality (`f:`), and type/text filters, sorted `order:edhrec`
2. Present name, mana cost, oracle text, and price
3. Only call `get_card_data` if the user wants deeper detail on specific cards

### Price checking
- **Current price:** `get_card_data(["Card Name"])` - includes USD, foil, etched, EUR, tix
- **Cheapest printing:** `get_card_prints("Card Name")` - every printing with prices
- **Budget alternatives:** `search_cards("o:similar_effect f:format usd<=2")`

### Rules questions
1. Check if oracle text from `search_cards` or `get_card_data` already answers it
2. If the interaction is complex, call `get_rulings` for official clarifications
3. Combine rules knowledge with rulings data for a complete answer

### Comparing cards
`get_card_data(["Card A", "Card B", "Card C"])` - one batched call, then compare stats, text, prices, and EDHREC rank.

## Scryfall Search Syntax

Full reference: `references/scryfall-syntax.md`

| Filter | Syntax | Example |
|---|---|---|
| Color identity | `id<=COLORS` | `id<=bg` |
| Card type | `t:TYPE` | `t:creature`, `t:legendary` |
| Oracle text | `o:"TEXT"` | `o:"draw a card"` |
| Mana value | `mv<=N` / `mv=N` / `mv>=N` | `mv<=3` |
| Format legal | `f:FORMAT` | `f:commander`, `f:modern` |
| Power/toughness | `pow>=N`, `tou>=N` | `pow>=5` |
| Rarity | `r:RARITY` | `r:mythic` |
| Set | `s:CODE` | `s:mh3` |
| Keywords | `keyword:KEYWORD` | `keyword:flying` |
| Sort order | `order:ORDER` | `order:edhrec`, `order:usd` |
| Price filter | `usd<=N` | `usd<=1` |
| Is commander | `is:commander` | Legendary creatures + special commanders |
| Color | `c:COLORS` | `c:r`, `c>=rg` |

Combine freely: `t:creature id<=ur mv<=3 o:"when ~ enters" f:commander order:edhrec`

## Presenting Results

- Always include card name and mana cost
- Include oracle text when the user is evaluating what a card does
- Include price when the user is budget-conscious or comparing printings
- Link `scryfall_uri` so the user can see the card page with art and full details
- Note EDHREC rank to indicate popularity when relevant
- For Commander suggestions, group by role (ramp, removal, card draw, etc.) rather than a flat list
