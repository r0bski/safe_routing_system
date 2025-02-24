import polars as pl
import json
import math

FILE_NAME = "../compiled_data.parquet"



def crime_heatmap():
    df=pl.read_parquet(FILE_NAME)
    df = df.filter(
        (pl.col("Longitude").is_not_null()) &
        (pl.col("Latitude").is_not_null())
    )
    df = add_score_to_df(df)

    heat_points = []
    for row in df.iter_rows():
        lon = row[0]
        lat = row[1]
        score = row[3]
        # Skip if missing or invalid
        if lat is not None and lon is not None:
            # Convert lat/lon to float
            heat_points.append([float(lat), float(lon), float(score)])


    return heat_points



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
        scores.append(crime_score_dict.get(crime_type, 1))

    df = df.with_columns(pl.Series("Score", scores))
    
    # Ensure the Score column is typed as integer
    df = df.with_columns(pl.col("Score").cast(pl.Int64))
    return df


if __name__ == "__main__":
    heat_data = crime_heatmap()