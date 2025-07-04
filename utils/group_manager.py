"""Utility functions for managing image selection groups."""

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

