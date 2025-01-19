#!/usr/bin/env python3

"""
Precompute crime-based costs for each edge in London's walking network.
Requires: pip install osmnx polars shapely rtree geopy
Usage:
    python precompute_edge_crime_costs.py
"""

import os
import polars as pl
import osmnx as ox
import networkx as nx

from shapely.geometry import Point, LineString
from rtree import index
from geopy.distance import geodesic

# ------------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------------
CRIME_PARQUET_PATH = "../compiled_data.parquet"  # Adjust path as needed
GRAPHML_OUTPUT_PATH = "london_with_crime.graphml"
PLACE_NAME = "London, England, United Kingdom"

SEARCH_RADIUS_KM = 0.1  # ~100 meters around the edge midpoint


# ------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ------------------------------------------------------------------

def add_score_to_df(df: pl.DataFrame) -> pl.DataFrame:
    df = df.select(["Longitude", "Latitude", "Crime type"])
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
        scores.append(crime_score_dict.get(crime_type, 1))  # int

    df = df.with_columns(pl.Series("Score", scores))
    
    # Ensure the Score column is typed as integer
    df = df.with_columns(pl.col("Score").cast(pl.Int64))
    return df

def build_crime_rtree(crime_df: pl.DataFrame) -> index.Index:
    """
    Build an R-tree for fast spatial lookups.
    Each entry's 'obj' will store the crime score.
    """
    crime_idx = index.Index()
    for i, row in enumerate(crime_df.iter_rows()):
        lon, lat, score = row[0], row[1], row[3]
        pt = Point(lon, lat)
        crime_idx.insert(i, pt.bounds, obj=score)
    return crime_idx


def compute_edge_crime_cost(u, v, data, G, crime_index, radius_km=0.1):
    """
    Compute a 'cost' for edge (u, v) that combines:
      - distance (in km)
      - sum of crime scores within ~radius_km of the edge midpoint.
    """
    # 1) Base distance in km
    base_dist_m = data.get("length", 0)
    base_dist_km = base_dist_m / 1000.0

    # 2) Get the edge geometry (or fallback to node positions)
    geom = data.get("geometry", None)
    if geom is None:
        lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
        lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
        line = LineString([(lon1, lat1), (lon2, lat2)])
    else:
        line = geom

    # 3) Find midpoint of the edge
    midpoint = line.interpolate(0.5, normalized=True)
    mid_lon, mid_lat = midpoint.x, midpoint.y

    # 4) Build a bounding box in degrees for the R-tree intersection
    #    (We do a coarse bounding box, then refine if needed.)
    #    ~1 degree of lat ~111 km, so for radius_km:
    deg_approx = radius_km / 111.0
    minx = mid_lon - deg_approx
    maxx = mid_lon + deg_approx
    miny = mid_lat - deg_approx
    maxy = mid_lat + deg_approx

    # 5) Query the R-tree for crimes in that bounding box
    hits = crime_index.intersection((minx, miny, maxx, maxy), objects=True)
    
    # 6) Sum up crime scores. Optionally do precise distance checks.
    crime_score_sum = 0
    for item in hits:
        crime_score = int(item.object)  # we stored the score in obj
        crime_score_sum += crime_score

    # 7) Combine distance with crime factor
    return base_dist_km + 0.01 * crime_score_sum


def precompute_crime_weights(G, crime_df, radius_km=0.1):
    """
    Precompute 'custom_weight' for each edge in the graph using an R-tree
    to quickly sum nearby crime scores.
    """
    print("Building R-tree from crime data...")
    rtree_index = build_crime_rtree(crime_df)

    print("Computing crime-based cost for edges...")
    edge_count = len(G.edges())
    for i, (u, v, key, data) in enumerate(G.edges(keys=True, data=True), 1):
        if i % 1000 == 0:
            print(f"  Processed {i}/{edge_count} edges...")
        cost = compute_edge_crime_cost(u, v, data, G, rtree_index, radius_km)
        data["custom_weight"] = cost

    return G


# ------------------------------------------------------------------
# 3. MAIN SCRIPT
# ------------------------------------------------------------------

def main():
    print("Loading crime data...")
    crime_data = pl.read_parquet("/Users/robertbulcock/Projects/safe_routing_system/compiled_data.parquet")
    crime_data = crime_data.filter(
        (pl.col("Longitude").is_not_null()) &
        (pl.col("Latitude").is_not_null())
    )
    crime_data = add_score_to_df(crime_data)
    print(crime_data)

    print("Loading London walk network with OSMnx...")
    G = ox.graph_from_place(PLACE_NAME, network_type='walk')
    if not G.graph.get("simplified", False):
        G = ox.simplify_graph(G)
    else:
        print("Graph is already simplified, skipping simplify_graph.")
        

    print("Precomputing edge weights...")
    G = precompute_crime_weights(G, crime_data, SEARCH_RADIUS_KM)

    print(f"Saving final graph to {GRAPHML_OUTPUT_PATH}...")
    ox.save_graphml(G, GRAPHML_OUTPUT_PATH)
    print("Done!")


if __name__ == "__main__":
    main()