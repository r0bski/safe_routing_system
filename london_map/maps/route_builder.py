import osmnx as ox
import networkx as nx
from geopy.distance import geodesic


def calc_route(start_coords, end_coords):
    """
    Loads a precomputed graph with 'custom_weight' on each edge
    and performs A* to find a route.
    """
    print("Loading Graph")
    # 1) Load the precomputed graph
    #    This graph already has data["custom_weight"] stored
    G = ox.load_graphml("london_with_crime.graphml")
    print("Graph loaded")
    for u, v, k, data in G.edges(keys=True, data=True):
    # Check if the attribute exists and is not already float
        if "custom_weight" in data:
        # Convert from str -> float
            data["custom_weight"] = float(data["custom_weight"])
    print("Conversion done")

    # 2) Convert node IDs to integers if needed
    #    (NetworkX can sometimes store them as strings from GraphML)
    #    If they're already int, skip this step.
    #G = ox.utils_graph.convert_node_labels_to_integers(G, discard_old_labels=False)

    # 3) Find the nearest node to start/end
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    start_node = ox.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.nearest_nodes(G, end_lon, end_lat)

    # 4) Define a simple distance heuristic for A*
    def heuristic(u, v):
        lat_u = G.nodes[u]["y"]
        lon_u = G.nodes[u]["x"]
        lat_v = G.nodes[v]["y"]
        lon_v = G.nodes[v]["x"]
        return geodesic((lat_u, lon_u), (lat_v, lon_v)).km

    # 5) Run A* referencing the precomputed weight
    try:
        path_nodes = nx.astar_path(
            G,
            source=start_node,
            target=end_node,
            weight="custom_weight",  # uses your precomputed cost
            heuristic=heuristic
        )
        return path_nodes
    except nx.NetworkXNoPath:
        return None

# Example test
if __name__ == "__main__":
    route = calc_route((51.5079, -0.0877), (51.5033, -0.0832))
    print("Route node IDs:", route)