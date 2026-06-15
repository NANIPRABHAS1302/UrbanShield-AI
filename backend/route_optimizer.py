"""Route optimization wrapper around the NetworkX graph analyzer."""

from __future__ import annotations

from typing import Any

from .ai_modules.gnn_module import GraphSafetyAnalyzer
from .data_store import JsonDataStore


class RouteOptimizer:
    """Builds safest, balanced, and fastest route candidates."""

    def __init__(self, store: JsonDataStore, graph_analyzer: GraphSafetyAnalyzer) -> None:
        self.store = store
        self.graph_analyzer = graph_analyzer

    def alternatives(self, start_zone: str, end_zone: str, women_mode: bool = False) -> list[dict[str, Any]]:
        seen = set()
        candidates = []
        for preference in ["safest", "balanced", "fastest"]:
            route = self.graph_analyzer.find_path(start_zone, end_zone, preference=preference, women_mode=women_mode)
            route_key = tuple(route)
            if route_key in seen:
                continue
            seen.add(route_key)
            candidates.append(
                {
                    "preference": preference,
                    "zone_ids": route,
                    "metrics": self.graph_analyzer.route_metrics(route),
                }
            )
        return candidates
