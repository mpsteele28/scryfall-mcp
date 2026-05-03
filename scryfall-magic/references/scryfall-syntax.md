# Scryfall Search Syntax Reference

This is the complete Scryfall search syntax you can use with `search_cards`. Combine any of these filters in a single query string.

## Color & Identity

| Syntax | Meaning | Example |
|---|---|---|
| `c:W` | Card is white | `c:W` |
| `c:WUBRG` | Card is all five colors | `c:WUBRG` |
| `c>=RG` | Card is at least red and green | `c>=RG` |
| `c<=UB` | Card is at most blue and black | `c<=UB` |
| `c=RG` | Card is exactly red and green | `c=RG` |
| `id:COLORS` | Color identity includes COLORS | `id:BRG` |
| `id<=COLORS` | Color identity within COLORS (for Commander) | `id<=WU` |
| `id=COLORS` | Color identity exactly COLORS | `id=WUBRG` |

Color symbols: W (white), U (blue), B (black), R (red), G (green), C (colorless)

## Card Types

| Syntax | Meaning | Example |
|---|---|---|
| `t:creature` | Creature cards | `t:creature` |
| `t:instant` | Instants | `t:instant` |
| `t:sorcery` | Sorceries | `t:sorcery` |
| `t:enchantment` | Enchantments | `t:enchantment` |
| `t:artifact` | Artifacts | `t:artifact` |
| `t:planeswalker` | Planeswalkers | `t:planeswalker` |
| `t:land` | Lands | `t:land` |
| `t:legendary` | Legendary permanents | `t:legendary` |
| `t:snow` | Snow permanents | `t:snow` |
| `t:"human wizard"` | Multi-word type | `t:"human wizard"` |

## Mana & Cost

| Syntax | Meaning | Example |
|---|---|---|
| `mv=N` | Mana value exactly N | `mv=3` |
| `mv<=N` | Mana value at most N | `mv<=2` |
| `mv>=N` | Mana value at least N | `mv>=7` |
| `m:{W}{W}` | Mana cost contains {W}{W} | `m:{2}{G}` |
| `manavalue=N` | Same as mv=N | `manavalue=5` |

## Card Text

| Syntax | Meaning | Example |
|---|---|---|
| `o:"text"` | Oracle text contains | `o:"draw a card"` |
| `o:/regex/` | Oracle text matches regex | `o:/\+1\/\+1 counter/` |
| `fo:"text"` | Full oracle text (includes reminder) | `fo:"can't be blocked"` |
| `keyword:KW` | Has keyword ability | `keyword:flying` |
| `keyword:deathtouch` | Has deathtouch | `keyword:deathtouch` |

Common keywords: flying, trample, deathtouch, lifelink, haste, vigilance, menace, reach, flash, hexproof, indestructible, double strike, first strike, ward, defender

## Power, Toughness, Loyalty

| Syntax | Meaning | Example |
|---|---|---|
| `pow=N` | Power exactly N | `pow=4` |
| `pow>=N` | Power at least N | `pow>=5` |
| `pow<=N` | Power at most N | `pow<=1` |
| `tou=N` | Toughness exactly N | `tou=1` |
| `tou>=N` | Toughness at least N | `tou>=6` |
| `loy=N` | Starting loyalty N | `loy=4` |

## Format Legality

| Syntax | Meaning |
|---|---|
| `f:standard` | Legal in Standard |
| `f:modern` | Legal in Modern |
| `f:legacy` | Legal in Legacy |
| `f:vintage` | Legal in Vintage |
| `f:commander` | Legal in Commander/EDH |
| `f:pioneer` | Legal in Pioneer |
| `f:pauper` | Legal in Pauper |
| `f:historic` | Legal in Historic |
| `f:brawl` | Legal in Brawl |
| `banned:commander` | Banned in Commander |
| `restricted:vintage` | Restricted in Vintage |

## Set & Rarity

| Syntax | Meaning | Example |
|---|---|---|
| `s:CODE` | From specific set | `s:mh3` |
| `r:common` | Common rarity | `r:common` |
| `r:uncommon` | Uncommon | `r:uncommon` |
| `r:rare` | Rare | `r:rare` |
| `r:mythic` | Mythic rare | `r:mythic` |
| `year=YYYY` | Printed in year | `year=2024` |
| `year>=YYYY` | Printed in or after year | `year>=2020` |

## Prices

| Syntax | Meaning | Example |
|---|---|---|
| `usd<=N` | USD price at most N | `usd<=1` |
| `usd>=N` | USD price at least N | `usd>=50` |
| `usd=N` | USD price exactly N | `usd=0.25` |
| `eur<=N` | EUR price at most N | `eur<=5` |
| `tix<=N` | MTGO tix at most N | `tix<=2` |

## Special Filters

| Syntax | Meaning |
|---|---|
| `is:commander` | Can be a Commander (legendary creatures + special cards) |
| `is:spell` | Non-land cards |
| `is:permanent` | Permanent cards |
| `is:modal` | Modal DFCs |
| `is:transform` | Transforming DFCs |
| `is:split` | Split cards |
| `is:flip` | Flip cards |
| `is:meld` | Meld cards |
| `is:reprint` | Reprinted cards |
| `not:reprint` | Original printings only |
| `is:funny` | Un-set/joke cards |
| `is:token` | Token cards |
| `has:watermark` | Has a watermark |
| `produces:G` | Produces green mana |
| `produces>=RG` | Produces at least red and green mana |

## Sorting

| Syntax | Meaning |
|---|---|
| `order:name` | Alphabetical |
| `order:usd` | Price (highest first) |
| `order:edhrec` | EDHREC popularity (most played first) |
| `order:cmc` | Mana value ascending |
| `order:power` | Power descending |
| `order:toughness` | Toughness descending |
| `order:released` | Release date (newest first) |
| `order:rarity` | Rarity (mythic first) |
| `order:review` | Community review score |
| `direction:asc` | Ascending (combine with order) |
| `direction:desc` | Descending (combine with order) |

## Boolean Operators

| Syntax | Meaning | Example |
|---|---|---|
| (space) | AND (default) | `t:creature c:R` = red creatures |
| `or` | OR | `t:angel or t:demon` |
| `-` | NOT (negate) | `-t:creature` = non-creatures |
| `()` | Grouping | `(t:angel or t:demon) c:WB` |

## Example Compound Queries

Find the best budget creatures for a Golgari Commander deck:
```
t:creature id<=bg f:commander usd<=2 order:edhrec
```

Find all legendary creatures that draw cards, for Commander:
```
t:legendary t:creature o:"draw" f:commander is:commander order:edhrec
```

Find cheap instant-speed removal in blue-white:
```
(t:instant or (t:creature keyword:flash)) id<=wu o:"destroy" f:commander usd<=1 order:edhrec
```

Find board wipes legal in Modern:
```
(o:"destroy all" or o:"all creatures get" or o:"exile all") f:modern order:edhrec
```

Find dual lands for a 3-color deck:
```
t:land id<=wub produces>=WU -t:basic f:commander order:edhrec
```
