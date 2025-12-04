# core/services/graph.py
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import heapq

from core.models import POI, PoiEdge


@dataclass
class PathResult:
    travel_time_s: int
    poi_ids: List[int]


class PoiGraph:
    def __init__(self, adjacency: Dict[int, List[Tuple[int, int]]]):
        self.adjacency = adjacency

    @classmethod
    def from_db(cls) -> "PoiGraph":
        from collections import defaultdict
        adj = defaultdict(list)
        edges = PoiEdge.objects.all().select_related("from_poi", "to_poi")
        for e in edges:
            a, b, t = e.from_poi_id, e.to_poi_id, e.travel_time_s
            adj[a].append((b, t))
            adj[b].append((a, t))  # undirected
        return cls(dict(adj))

    def shortest_path(self, start_id: int, end_id: int) -> PathResult:
        if start_id == end_id:
            return PathResult(travel_time_s=0, poi_ids=[start_id])

        adjacency = self.adjacency
        INF = 10**15
        dist: Dict[int, int] = {}
        prev: Dict[int, Optional[int]] = {}

        for node in adjacency.keys():
            dist[node] = INF
            prev[node] = None
        dist[start_id] = 0

        heap: List[Tuple[int, int]] = [(0, start_id)]

        while heap:
            current_dist, node = heapq.heappop(heap)
            if current_dist > dist[node]:
                continue
            if node == end_id:
                break
            for neighbor, w in adjacency.get(node, []):
                nd = current_dist + w
                if nd < dist[neighbor]:
                    dist[neighbor] = nd
                    prev[neighbor] = node
                    heapq.heappush(heap, (nd, neighbor))

        if dist[end_id] == INF:
            raise ValueError(f"No route from POI {start_id} to {end_id}")

        path_ids: List[int] = []
        cur = end_id
        while cur is not None:
            path_ids.append(cur)
            cur = prev[cur]
        path_ids.reverse()

        return PathResult(travel_time_s=dist[end_id], poi_ids=path_ids)


# simple module-level cache for graph
_graph_cache: Optional[PoiGraph] = None


def get_graph(force_reload: bool = False) -> PoiGraph:
    global _graph_cache
    if _graph_cache is None or force_reload:
        _graph_cache = PoiGraph.from_db()
    return _graph_cache


def get_travel_time_and_route(a: POI, b: POI) -> PathResult:
    graph = get_graph()
    return graph.shortest_path(a.id, b.id)


def get_travel_time_s(a: POI, b: POI) -> int:
    return get_travel_time_and_route(a, b).travel_time_s

