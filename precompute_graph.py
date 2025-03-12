"""
Precompute crime-based costs for each edge in London's walking network.
"""

import polars as pl
import osmnx as ox
from shapely.geometry import Point, LineString
from rtree import index


# Define paths and constants
CRIME_PARQUET_PATH = "./compiled_data.parquet"
GRAPHML_OUTPUT_PATH = "london_map/london_with_combined_data.graphml"

PLACE_NAME = "London, England, United Kingdom"
SEARCH_RADIUS_KM = 0.1  # ~100 meters around the edge midpoint




def add_score_to_df(df: pl.DataFrame) -> pl.DataFrame:
    """Add risk score column to each crime. 5 being crimes that must be avoided the most
        and 1 being crimes that arn't dangerous like fraud and shoplifting


    Args:
        df (pl.DataFrame): Dataframe containg all crimes

    Returns:
        pl.DataFrame: Dataframe with added risk score column
    """
    # Filter all unneeded coloumns to reduce memory usage
    df = df.select(["Longitude", "Latitude", "Crime type"])
    # Define dictionary with crime types and risk scores
    crime_score_dict = {
        "Violence and sexual offences": 5,
        "Other theft": 1,
        "Anti-social behaviour": 4,
        "Criminal damage and arson": 2,
        "Drugs": 3,
        "Public order": 5,
        "Robbery": 5,
        "Vehicle crime": 2,
        "Other crime": 1,
        "Burglary": 2,
        "Possession of weapons": 5,
        "Theft from the person": 5,
        "Bicycle theft": 2,
        "Shoplifting": 1
    }
    scores = []
    # Make a list of all the scores of each crime
    for crime_type in df["Crime type"]:
        scores.append(crime_score_dict.get(crime_type, 1))  # int

    # Add scores list as a column to the dataframe
    df = df.with_columns(pl.Series("Score", scores))
    
    # Ensure the scores are stored as integers
    df = df.with_columns(pl.col("Score").cast(pl.Int64))
    return df

def build_crime_rtree(crime_df: pl.DataFrame) -> index.Index:
    """Build an R-tree for fast spatial lookups to reduce runtime.
        Each entry"s object will store the crime score.

    Args:
        crime_df (pl.DataFrame): Dataframe containing long, lat, Crime Type and Score

    Returns:
        index.Index: R-tree containing all crimes
    """
    # initulise R-Tree
    crime_idx = index.Index()
    # Iterate through dataframe
    for i, row in enumerate(crime_df.iter_rows()):
        lon, lat, score = row[0], row[1], row[3]
        pt = Point(lon, lat)
        # Insert crime into R-tree
        crime_idx.insert(i, pt.bounds, obj=score)
    return crime_idx


def compute_edge_crime_cost(u, v, data, G, crime_index, radius_km=0.1):
    """Compute a weight for edge (u, v) that combines distance in km and 
        sum of crime scores within radius_km of the edge midpoint.

    Args:
        u (_type_): _description_
        v (_type_): _description_
        data (_type_): _description_
        G (MultiDiGraph): Road network of London
        crime_index (_type_): R-tree contining each crime
        radius_km (float, optional): Used to consider crimes near the edge. Defaults to 0.1.

    Returns:
        float: Crime factor calclated using crime scores and distance of crimes away from edge
    """
    # Base distance in km
    base_dist_m = data.get("length", 0)
    base_dist_km = base_dist_m / 1000.0

    # Get the edge geometry
    geom = data.get("geometry", None)
    if geom is None:
        lat1, lon1 = G.nodes[u]["y"], G.nodes[u]["x"]
        lat2, lon2 = G.nodes[v]["y"], G.nodes[v]["x"]
        line = LineString([(lon1, lat1), (lon2, lat2)])
    else:
        line = geom

    # Find midpoint of the edge
    midpoint = line.interpolate(0.5, normalized=True)
    mid_lon, mid_lat = midpoint.x, midpoint.y

    # Build a bounding box in degrees for the R-tree intersection
    # 1 degree of lat is aproximatly 111 km, so for radius_km:
    deg_approx = radius_km / 111.0
    min_x = mid_lon - deg_approx
    max_x = mid_lon + deg_approx
    min_y = mid_lat - deg_approx
    max_y = mid_lat + deg_approx

    # Get crimes in bounding box from R-tree
    hits = crime_index.intersection((min_x, min_y, max_x, max_y), objects=True)
    
    # Sum up crime scores
    crime_score_sum = 0
    for item in hits:
        # Get score attribute of each crime obj
        crime_score = int(item.object)
        crime_score_sum += crime_score

    # Combine distance with crime factor
    return base_dist_km + 0.01 * crime_score_sum


def precompute_crime_weights(G, crime_df: pl.DataFrame, radius_km=0.1):
    """Precompute "custom_weight" for each edge in the graph using an R-tree
        to quickly sum nearby crime scores.

    Args:
        G (MultiDiGraph): Road network of London
        crime_df (pl.DataFrame): Crime Dataframe
        radius_km (float, optional): Size of radius. Defaults to 0.1.

    Returns:
        MultiDiGraph: London road network with added custom safty weights on each node and edge
    """

    print("Building R-tree from crime data")
    rtree_index = build_crime_rtree(crime_df)

    print("Computing crime-based cost for edges")
    edge_count = len(G.edges())
    # Loop through every edge in network
    for i, (u, v, key, data) in enumerate(G.edges(keys=True, data=True), 1):
        # Print progress every 1000 edges processed
        if i % 10000 == 0:
            print(f"  Processed {i}/{edge_count} edges")
        # Calucilate the crime cost of the edge
        cost = compute_edge_crime_cost(u, v, data, G, rtree_index, radius_km)

        base_dist_m = data.get("length", 0)
        data["safty_score"] = cost

        # Add the cost as a custom weight to the graph
        data["custom_weight"] = cost + 0.1 * base_dist_m

        # Also create a combined weight = crime-based cost + length
        data["combined_weight"] = cost + 0.25 * base_dist_m


    return G



def main():
    print("Loading crime data...")
    # Load crime data
    crime_data = pl.read_parquet(CRIME_PARQUET_PATH)
    # Filter null long/ lat rows from dataframe
    crime_data = crime_data.filter(
        (pl.col("Longitude").is_not_null()) &
        (pl.col("Latitude").is_not_null())
    )
    # Add saftey scores
    crime_data = add_score_to_df(crime_data)

    print("Loading London walk network with OSMnx")
    # Load London road network
    """
    G = ox.graph_from_place(PLACE_NAME, network_type="walk")
    # Try simplifying graph
    if not G.graph.get("simplified", False):
        G = ox.simplify_graph(G)
    else:
        print("Graph is already simplified, skipping simplify_graph.")
    """
    G = ox.load_graphml("london_map/london_with_crime.graphml")

    print("Precomputing edge weights")
    # Add crime score to each road and intersection
    G = precompute_crime_weights(G, crime_data, SEARCH_RADIUS_KM)

    print(f"Saving final graph to {GRAPHML_OUTPUT_PATH}")
    # Save graph
    ox.save_graphml(G, GRAPHML_OUTPUT_PATH)
    print("Done!")


if __name__ == "__main__":
    main()