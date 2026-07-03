from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..schemas import DistributedNode


@dataclass
class DistributedState:
    nodes: dict[str, DistributedNode] = field(default_factory=dict)


class DistributedService:
    def __init__(self):
        self.state = DistributedState()

    def list_nodes(self) -> list[dict[str, Any]]:
        return [node.model_dump() for node in self.state.nodes.values()]

    def upsert_node(self, node: DistributedNode) -> dict[str, Any]:
        self.state.nodes[node.name] = node
        return node.model_dump()

    def remove_node(self, name: str) -> bool:
        return self.state.nodes.pop(name, None) is not None

    def shard(self, item_ids: list[int], mode: str = "many-to-one") -> dict[str, Any]:
        workers = [node for node in self.state.nodes.values() if node.enabled and node.role == "worker"]
        if not workers:
            return {"mode": mode, "shards": [{"node": "local", "items": item_ids}]}
        shards = [{"node": node.name, "base_url": node.base_url, "items": []} for node in workers]
        for idx, item_id in enumerate(item_ids):
            shards[idx % len(shards)]["items"].append(item_id)
        return {"mode": mode, "shards": shards}
