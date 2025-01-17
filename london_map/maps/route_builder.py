import polars as pl
import osmnx as ox
import networkx as nx
from shapely.geometry import LineString
from geopy.distance import geodesic
import math

def calc_route(start_coords, dest_coords):
    crime_data = pl.read_parquet("../compiled_data.parquet")
    crime_data = add_score_to_df(crime_data)
    road_network = load_network()
    path_nodes = a_star(road_network, crime_data, start_coords, dest_coords)
    return path_nodes

def add_score_to_df(df: pl.DataFrame) -> pl.DataFrame:
    df = df.select("Longitude", "Latitude", "Crime type")
    crime_score_dict = {
        'Violence and sexual offences': 5, 
        'Other theft': 1, 
        'Anti-social behaviour': 4,
        'Criminal damage and arson': 2, 
        'Drugs': 3, 
        'Public order': 5, 
        'Robbery': 5, 
        'Vehicle crime': 2, 
        'Other crime': 1, 
        'Burglary': 2, 
        'Possession of weapons': 5, 
        'Theft from the person': 5, 
        'Bicycle theft': 2, 
        'Shoplifting': 1
    }
    scores = []
    for crime_type in df["Crime type"]:
        scores.append(crime_score_dict.get(crime_type, 1))
    return df.with_columns(pl.Series("Score", scores))

def load_network():
    place_name = "London, England, United Kingdom"
    graph = ox.graph_from_place(place_name, network_type='walk')
    graph = ox.simplify_graph(graph)
    return graph

def compute_edge_weight(u, v, data, crime_data, G, search_radius=0.1):
    base_dist_m = data.get("length", 0)
    base_dist_km = base_dist_m / 1000.0

    geom = data.get("geometry", None)
    if geom is None:
        # fallback: use node coords
        lat1 = G.nodes[u]['y']
        lon1 = G.nodes[u]['x']
        lat2 = G.nodes[v]['y']
        lon2 = G.nodes[v]['x']
        line = LineString([(lon1, lat1), (lon2, lat2)])
    else:
        line = geom

    midpoint = line.interpolate(0.5, normalized=True)
    mid_lon, mid_lat = midpoint.x, midpoint.y

    # approximate bounding box
    deg_approx = search_radius / 111.0
    min_lat = mid_lat - deg_approx
    max_lat = mid_lat + deg_approx
    min_lon = mid_lon - deg_approx
    max_lon = mid_lon + deg_approx

    subset = crime_data.filter(
        (pl.col("Latitude") >= min_lat) & 
        (pl.col("Latitude") <= max_lat) &
        (pl.col("Longitude") >= min_lon) &
        (pl.col("Longitude") <= max_lon)
    )

    crime_score_sum = 0
    for row in subset.iter_rows():
        c_lon, c_lat, c_score = row[0], row[1], row[2]
        # In a real approach, you'd do an actual distance check from midpoint
        crime_score_sum += c_score

    # Weighted cost = distance + factor * crime
    cost = base_dist_km + 0.01 * crime_score_sum
    return cost

def a_star(road_network, crime_data, start, end):
    start_lat, start_lon = start
    end_lat, end_lon = end

    start_node = ox.nearest_nodes(road_network, start_lon, start_lat)
    end_node = ox.nearest_nodes(road_network, end_lon, end_lat)

    # Precompute custom weights
    for u, v, key, data in road_network.edges(keys=True, data=True):
        w = compute_edge_weight(u, v, data, crime_data, road_network, 0.1)
        data["custom_weight"] = w

    # A* with geodesic distance as a heuristic
    def heuristic(n1, n2):
        lat1, lon1 = road_network.nodes[n1]['y'], road_network.nodes[n1]['x']
        lat2, lon2 = road_network.nodes[n2]['y'], road_network.nodes[n2]['x']
        return geodesic((lat1, lon1), (lat2, lon2)).km

    try:
        path_nodes = nx.astar_path(
            road_network, 
            start_node, 
            end_node, 
            heuristic=heuristic, 
            weight='custom_weight'
        )
        return path_nodes
    except nx.NetworkXNoPath:
        return None

# Testing
if __name__ == "__main__":
    # Example: let's assume the user inputs (lat, lon) for London
    # e.g., start: near "London Bridge", end: near "Waterloo Station"
    # This is just illustrative coords
    route = calc_route((51.5079, -0.0877), (51.5033, -0.0832))
    print("Route node IDs:", route)