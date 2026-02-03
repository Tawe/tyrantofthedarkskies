"""
Loot system per docs/loot_system.md.

- Generate loot once on death (guaranteed, tables, chance, coins).
- Supports legacy creature loot.entries format.
"""

import random
from typing import Dict, List, Any, Optional


def generate_loot(
    loot_config: Dict,
    loot_tables: Optional[Dict[str, Dict]] = None,
    items_dict: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Generate loot from a creature template loot block.
    Returns { "rolled": True, "coins": int, "items": [ {"item_id": str, "count": int}, ... ] }.
    Supports new format (guaranteed, tables, chance, coins) and legacy (entries with item/chance).
    """
    loot_tables = loot_tables or {}
    items_dict = items_dict or {}
    out_items: List[Dict[str, Any]] = []
    out_coins = 0

    # Legacy format: loot.entries with { "item": item_id, "chance": 0-100 }
    entries = loot_config.get("entries")
    if entries is not None:
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            item_id = entry.get("item")
            if not item_id or not items_dict.get(item_id):
                continue
            chance = entry.get("chance", 100)
            if random.randint(1, 100) <= chance:
                count = entry.get("count", 1)
                _add_item(out_items, item_id, count)
        return {"rolled": True, "coins": 0, "items": out_items}

    # New format
    # Guaranteed
    for g in loot_config.get("guaranteed") or []:
        if not isinstance(g, dict):
            continue
        item_id = g.get("item_id") or g.get("item")
        if not item_id or not items_dict.get(item_id):
            continue
        count = g.get("count", 1)
        _add_item(out_items, item_id, count)

    # Tables (weighted loot tables)
    for t in loot_config.get("tables") or []:
        if not isinstance(t, dict):
            continue
        table_id = t.get("loot_table_id")
        rolls = t.get("rolls", 1)
        table = loot_tables.get(table_id) if table_id else None
        if not table or not isinstance(table.get("entries"), list):
            continue
        for _ in range(rolls):
            item_id, count = _roll_loot_table(table)
            if item_id and items_dict.get(item_id):
                _add_item(out_items, item_id, count)

    # Chance
    for c in loot_config.get("chance") or []:
        if not isinstance(c, dict):
            continue
        item_id = c.get("item_id") or c.get("item")
        if not item_id or not items_dict.get(item_id):
            continue
        chance = c.get("chance", 0.5)
        if random.random() <= chance:
            count = c.get("count", 1)
            _add_item(out_items, item_id, count)

    # Coins
    coins_cfg = loot_config.get("coins")
    if isinstance(coins_cfg, dict):
        lo = coins_cfg.get("min", 0)
        hi = coins_cfg.get("max", 0)
        out_coins = random.randint(lo, hi) if hi >= lo else lo
    elif isinstance(coins_cfg, (int, float)):
        out_coins = int(coins_cfg)

    return {"rolled": True, "coins": out_coins, "items": out_items}


def _add_item(items: List[Dict], item_id: str, count: int) -> None:
    """Merge item_id + count into items list (stack same item_id)."""
    for entry in items:
        if entry.get("item_id") == item_id:
            entry["count"] = entry.get("count", 0) + count
            return
    items.append({"item_id": item_id, "count": count})


def _roll_loot_table(table: Dict) -> tuple:
    """Pick one entry by weight; return (item_id, count)."""
    entries = table.get("entries") or []
    if not entries:
        return (None, 0)
    total = sum(e.get("weight", 1) for e in entries)
    if total <= 0:
        return (None, 0)
    r = random.randint(1, total)
    for e in entries:
        w = e.get("weight", 1)
        if r <= w:
            item_id = e.get("item_id") or e.get("item")
            lo = e.get("min", 1)
            hi = e.get("max", 1)
            count = random.randint(lo, hi) if hi >= lo else lo
            return (item_id, count)
        r -= w
    return (entries[-1].get("item_id") or entries[-1].get("item"), 1)
