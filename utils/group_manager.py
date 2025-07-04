"""Utility functions for managing image selection groups."""

import json
import os
from typing import Dict, Iterable, List

Group = List[List[str]]  # [[ext, img_id], ...]


def _unique_items(items: Iterable[Iterable[str]]) -> Group:
    seen = set()
    unique: Group = []
    for item in items:
        tup = tuple(item)
        if tup not in seen:
            seen.add(tup)
            unique.append(list(tup))
    return unique


def save_group(groups: Dict[str, Group], name: str, items: Iterable[Iterable[str]]) -> Dict[str, Group]:
    """Save a group of items under a given name."""
    if not name:
        return groups
    groups = groups.copy()
    groups[name] = _unique_items(items)
    return groups


def delete_groups(groups: Dict[str, Group], names: Iterable[str]) -> Dict[str, Group]:
    """Delete groups by name."""
    groups = groups.copy()
    for n in names:
        groups.pop(n, None)
    return groups


def rename_group(groups: Dict[str, Group], old: str, new: str) -> Dict[str, Group]:
    """Rename an existing group."""
    if old not in groups or not new:
        return groups
    groups = groups.copy()
    groups[new] = groups.pop(old)
    return groups


def duplicate_group(groups: Dict[str, Group], source: str, new: str) -> Dict[str, Group]:
    """Create a new group from an existing one."""
    if source not in groups or not new:
        return groups
    groups = groups.copy()
    groups[new] = groups[source].copy()
    return groups


def load_groups(groups: Dict[str, Group], names: Iterable[str]) -> Group:
    """Return combined unique items from the specified groups."""
    items: Group = []
    for n in names:
        items.extend(groups.get(n, []))
    return _unique_items(items)

def save_groups_file(groups: Dict[str, Group], path: str) -> None:
    """Write groups dictionary to ``path`` as JSON."""
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(path, "w") as f:
        json.dump(groups, f, indent=2)


def load_groups_file(path: str) -> Dict[str, Group]:
    """Load groups dictionary from ``path`` if it exists."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {}
    # ensure lists of lists
    groups: Dict[str, Group] = {}
    for k, v in data.items():
        groups[k] = [list(item) for item in v]
    return groups
