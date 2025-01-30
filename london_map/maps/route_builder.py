import osmnx as ox
import networkx as nx
from geopy.distance import geodesic

# Global variable (initially None)
GLOBAL_GRAPH = None

def get_graph():
    """
    Returns the precomputed graph, loading it once if needed.
    """
    global GLOBAL_GRAPH
    if GLOBAL_GRAPH is None:
        print("Loading graph from disk")
        GLOBAL_GRAPH = ox.load_graphml("london_with_crime.graphml")
    else:
        print("Graph already loaded")
    return GLOBAL_GRAPH

def get_route_edge_attributes(G, route, attribute):
    """
    Given a list of node IDs (route), return a list of `attribute`
    values for each edge along that route.
    """
    values = []
    for u, v in zip(route[:-1], route[1:]):
        edge_data = G[u][v][0] 
        val = edge_data.get(attribute, None)
        values.append(val)
    return values




def calc_route(start_coords, end_coords):
    """
    Loads a precomputed graph with 'custom_weight' on each edge
    and performs A* to find a route.
    """
    # Load the precomputed graph
    G = get_graph()

    for u, v, k, data in G.edges(keys=True, data=True):
    # Check if the attribute exists and is not already float
        if "custom_weight" in data:
        # Convert from str -> float
            data["custom_weight"] = float(data["custom_weight"])

    # Find the nearest node to start/end
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    start_node = ox.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.nearest_nodes(G, end_lon, end_lat)

    # Define a simple distance heuristic for A*
    def heuristic(u, v):
        lat_u = G.nodes[u]["y"]
        lon_u = G.nodes[u]["x"]
        lat_v = G.nodes[v]["y"]
        lon_v = G.nodes[v]["x"]
        return geodesic((lat_u, lon_u), (lat_v, lon_v)).km

    # Run A* referencing the precomputed weight
    try:
        # Find safest route
        safest_path_nodes = nx.astar_path(
            G,
            source=start_node,
            target=end_node,
            weight="custom_weight",  # uses precomputed safty weight
            heuristic=heuristic
        )
        # Find shortest route
        shortest_path_nodes = nx.astar_path(
            G,
            source=start_node,
            target=end_node,
            weight="length", 
            heuristic=heuristic
        )
    except nx.NetworkXNoPath:
        return None
    
    def convert_IDs_to_coords(path_nodes):
        # Convert node IDs to lat/lon pairs
        route_coords = []
        for node_id in path_nodes:
            lat = G.nodes[node_id]['y']
            lon = G.nodes[node_id]['x']
            route_coords.append([lat, lon])
        return route_coords
    
    # Get the lengths of all edges in each route
    lengths_safe = get_route_edge_attributes(G, safest_path_nodes, 'length')
    lengths_short = get_route_edge_attributes(G, shortest_path_nodes, 'length')
    # Sum up the lengths of each edge in the routes
    safe_len = sum(length for length in lengths_safe if length is not None)
    short_len = sum(length for length in lengths_short if length is not None)
    # Convert to km and round to 2 dp
    safe_len = safe_len/1000
    short_len = short_len/1000
    

    safe_route = convert_IDs_to_coords(safest_path_nodes)
    shortest_route = convert_IDs_to_coords(shortest_path_nodes)

    return safe_route, shortest_route, safe_len, short_len



# Example test
if __name__ == "__main__":
    route = calc_route((51.5079, -0.0877), (51.5033, -0.0832))
    print("Route node IDs:", route)