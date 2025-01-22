import polars as pl

df=pl.read_parquet("compiled_data.parquet")
df = df.filter(
        (pl.col("Longitude").is_not_null()) &
        (pl.col("Latitude").is_not_null())
    )

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
df=add_score_to_df(df)
df.write_parquet("crime_data_with_scores.parquet")