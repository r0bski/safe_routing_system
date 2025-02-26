import polars as pl

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


def crime_counts():
    df=pl.read_parquet(FILE_NAME)

    df = add_score_to_df(df)

    crime_totals = {
        'Violence and sexual offences': 0,
        'Other theft': 0,
        'Anti-social behaviour': 0,
        'Criminal damage and arson': 0,
        'Drugs': 0,
        'Public order': 0,
        'Robbery': 0,
        'Vehicle crime': 0,
        'Other crime': 0,
        'Burglary': 0,
        'Possession of weapons': 0,
        'Theft from the person': 0,
        'Bicycle theft': 0,
        'Shoplifting': 0,
        'Total number of crimes': 0
    }

    for row in df.iter_rows():
        for key in crime_totals.keys():
            if row[2] == key:
                crime_totals[key] = crime_totals[key] + 1
        crime_totals["Total number of crimes"] = (
                crime_totals["Total number of crimes"] +1 )
    
    return crime_totals


def generate_temporal_plot(filter:str = "All Crimes"):
    df = pl.read_parquet(FILE_NAME)
    df = df.filter(pl.col("Month").is_not_null())
    if filter != "All Crimes":
        df = df.filter(pl.col("Crime type") == filter)
    # Group by month and count
    df_agg = df.group_by("Month").agg(pl.len().alias("crime_count"))
    # Sort the months
    df_agg = df_agg.sort("Month")
    # Convert to a list of dicts or two parallel lists
    months = df_agg.select("Month").to_series().to_list()
    counts = df_agg.select("crime_count").to_series().to_list()
    line_data = {
        "labels": months,
        "data": counts
    }

    return line_data

if __name__ == "__main__":

    generate_temporal_plot()