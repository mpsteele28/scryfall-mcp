# MTG MCP

![Python](https://img.shields.io/badge/python-3.10+-blue)
![MCP](https://img.shields.io/badge/MCP-compatible-green)
![Scryfall](https://img.shields.io/badge/data-Scryfall-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A Model Context Protocol (MCP) server that gives Claude access to Magic: The Gathering card data via the [Scryfall API](https://scryfall.com/docs/api). No API key required.

## Tools

| Tool | Description |
|---|---|
| `search_cards` | Search cards using Scryfall syntax (type, color, cost, text, format, etc.) |
| `get_card_data` | Full card details for one or more named cards (batched) |
| `get_rulings` | Official rulings for a card |
| `get_card_prints` | All printings of a card with prices - use for "cheapest version" questions |
| `get_set_info` | Set metadata by set code |
| `get_random_card` | Random card, optionally filtered by a query |
| `autocomplete_card_name` | Name suggestions from a partial input |
| `download_image` | Save a card image to a local `MagicCards/` folder |

## Requirements

- Python 3.10+

## Installation

```bash
pip install -r requirements.txt
```

## Claude Desktop Setup

Add the server to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "scryfall": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

Config file location:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Claude Code Setup

Add to your project or global MCP config:

```bash
claude mcp add scryfall python /absolute/path/to/server.py
```

## Skill Guide

`scryfall-magic/SKILL.md` is a skill guide for Claude that teaches it how to pick the right tool and write efficient Scryfall queries. Install it via Claude Code:

```bash
claude skill install ./scryfall-magic
```

The skill reduces unnecessary API calls and gets better answers for deck building, price checking, and rules questions.

## Search Syntax

See `scryfall-magic/references/scryfall-syntax.md` for the full Scryfall search syntax reference, or visit [scryfall.com/docs/syntax](https://scryfall.com/docs/syntax).

Common filters:

```
t:creature id<=bg mv<=3 o:deathtouch f:commander order:edhrec
```
