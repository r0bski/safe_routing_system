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
        print("Loading graph from disk...")
        GLOBAL_GRAPH = ox.load_graphml("london_with_combined_data.graphml")
        print("Graph finished loading")
    else:
        print("Graph already loaded in memory")
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


def a_star(G, start_node, end_node, givern_weight:str):

    # Define a simple distance heuristic for A*
    def heuristic(u, v):
        lat_u = G.nodes[u]["y"]
        lon_u = G.nodes[u]["x"]
        lat_v = G.nodes[v]["y"]
        lon_v = G.nodes[v]["x"]
        return geodesic((lat_u, lon_u), (lat_v, lon_v)).km

    # Run A* referencing the precomputed weight
    try:
        # Find route
        path_nodes = nx.astar_path(
            G,
            source=start_node,
            target=end_node,
            weight=givern_weight,
            heuristic=heuristic
        )
        return path_nodes
    except nx.NetworkXNoPath:
        return None



def calc_route(start_coords, end_coords):
    """
    Loads a precomputed graph with 'custom_weight' on each edge
    and performs A* to find a route.
    """
    # Load the precomputed graph
    G = get_graph()

    for _, _, _, data in G.edges(keys=True, data=True):
    # Check if the attribute exists and is not already float
        if "custom_weight" in data:
        # Convert from str -> float
            data["custom_weight"] = float(data["custom_weight"])
        if "combined_weight" in data:
            data["combined_weight"] = float(data["combined_weight"])

    # Find the nearest node to start/end
    start_lat, start_lon = start_coords
    end_lat, end_lon = end_coords
    start_node = ox.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.nearest_nodes(G, end_lon, end_lat)


    # Run A* referencing the precomputed weight
    safest_path_nodes = a_star(G, start_node, end_node, "custom_weight")
    shortest_path_nodes = a_star(G, start_node, end_node, "length")
    balanced_path_nodes = a_star(G, start_node, end_node, "combined_weight")
    
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
    lengths_balanced = get_route_edge_attributes(G, balanced_path_nodes, "length")
    # Sum up the lengths of each edge in the routes
    safe_len = sum(length for length in lengths_safe if length is not None)
    short_len = sum(length for length in lengths_short if length is not None)
    balanced_len= sum(length for length in lengths_balanced if length is not None)
    # Convert to km and round to 2 dp
    safe_len = safe_len/1000
    short_len = short_len/1000
    balanced_len = balanced_len/1000
    

    safe_route = convert_IDs_to_coords(safest_path_nodes)
    shortest_route = convert_IDs_to_coords(shortest_path_nodes)
    balanced_route = convert_IDs_to_coords(balanced_path_nodes)

    return safe_route, shortest_route, balanced_route, safe_len, short_len, balanced_len



