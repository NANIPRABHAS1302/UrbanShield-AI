"""NetworkX-based graph safety module."""

from __future__ import annotations

from typing import Any, Callable

import networkx as nx

from ..data_store import JsonDataStore
from ..utils import clamp, mean


class GraphSafetyAnalyzer:
    """Uses a city mobility graph to score and optimize routes."""

    def __init__(self, store: JsonDataStore) -> None:
        self.store = store

    def build_graph(self) -> nx.Graph:
        graph = nx.Graph()
        zones = self.store.read_json("city_zones_metadata.json", default=[])
        danger = {
            item["zone_id"]: item.get("severity", 0.0)
            for item in self.store.read_json("danger_zones.json", default=[])
        }

        for zone in zones:
            node_risk = clamp(
                zone.get("crime_index", 0.3) * 0.4
                + (1 - zone.get("lighting_score", 0.7)) * 0.25
                + (1 - zone.get("cctv_coverage", 0.7)) * 0.2
                + danger.get(zone["id"], 0.0) * 0.15
            )
            graph.add_node(zone["id"], **zone, node_risk=node_risk)

        for edge in self.store.read_json("routes.json", default={"edges": []}).get("edges", []):
            source = edge["from"]
            target = edge["to"]
            source_risk = graph.nodes[source]["node_risk"]
            target_risk = graph.nodes[target]["node_risk"]
            edge_risk = clamp(1 - edge.get("base_safety", 0.6))
            graph.add_edge(
                source,
                target,
                **edge,
                edge_risk=edge_risk,
                risk_weight=edge.get("distance_km", 1.0) * (1 + edge_risk + mean([source_risk, target_risk])),
            )

        return graph

    def _weight_function(self, graph: nx.Graph, preference: str, women_mode: bool) -> Callable[[str, str, dict[str, Any]], float]:
        def weight(source: str, target: str, attrs: dict[str, Any]) -> float:
            source_node = graph.nodes[source]
            target_node = graph.nodes[target]
            low_light_penalty = mean(
                [1 - source_node.get("lighting_score", 0.7), 1 - target_node.get("lighting_score", 0.7)]
            )
            women_penalty = low_light_penalty * 1.4 if women_mode else 0.0

            if preference == "fastest":
                return attrs.get("travel_time_min", 10) + attrs.get("edge_risk", 0.3) * 4 + women_penalty * 6
            if preference == "balanced":
                return attrs.get("travel_time_min", 10) * 0.35 + attrs.get("risk_weight", 1.0) * 0.65 + women_penalty * 4
            return attrs.get("risk_weight", 1.0) + women_penalty

        return weight

    def find_path(self, start_zone: str, end_zone: str, preference: str = "safest", women_mode: bool = False) -> list[str]:
        graph = self.build_graph()
        if start_zone not in graph or end_zone not in graph:
            raise ValueError("Start or end zone does not exist")
        return nx.shortest_path(
            graph,
            source=start_zone,
            target=end_zone,
            weight=self._weight_function(graph, preference, women_mode),
        )

    def route_metrics(self, route: list[str]) -> dict[str, Any]:
        graph = self.build_graph()
        centrality = nx.betweenness_centrality(graph, weight="risk_weight", normalized=True)

        node_scores = [graph.nodes[zone_id]["node_risk"] for zone_id in route if zone_id in graph]
        edge_scores = []
        distance = 0.0
        travel_time = 0.0
        for source, target in zip(route, route[1:]):
            if not graph.has_edge(source, target):
                continue
            edge = graph.edges[source, target]
            edge_scores.append(edge.get("edge_risk", 0.35))
            distance += edge.get("distance_km", 0.0)
            travel_time += edge.get("travel_time_min", 0.0)

        centrality_exposure = mean([centrality.get(zone_id, 0.0) for zone_id in route])
        route_risk = clamp(mean(node_scores) * 0.62 + mean(edge_scores) * 0.28 + centrality_exposure * 0.1)

        return {
            "model": "NetworkX-GNN-Simplified",
            "route_risk": round(route_risk, 3),
            "node_risk_avg": round(mean(node_scores), 3),
            "edge_risk_avg": round(mean(edge_scores), 3),
            "centrality_exposure": round(centrality_exposure, 3),
            "distance_km": round(distance, 2),
            "travel_time_min": int(round(travel_time)),
        }
