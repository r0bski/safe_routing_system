import polars as pl 


dates =["2021-11", "2021-12", "2022-01", "2022-02", "2022-03", "2022-04",
        "2022-05", "2022-06", "2022-07", "2022-08", "2022-09", "2022-10",
        "2022-11", "2022-12", "2023-01", "2023-02", "2023-03", "2023-03",
        "2023-04", "2023-05", "2023-06", "2023-07", "2023-08", "2023-09",
        "2023-10", "2023-11", "2023-12", "2024-01", "2024-02", "2024-04",
        "2024-05", "2024-06", "2024-07", "2024-08", "2024-09", "2024-10"]

count=0
for date in dates:
    path = f"police_data/{date}/{date}-metropolitan-street.csv"
    if count==0:

        df = pl.read_csv(path)
    else:
        df_new = pl.read_csv(path)
        # Ensure the columns match
        if set(df.columns) == set(df_new.columns):
            # Append the new data to the bottom of the existing DataFrame
            df = df.vstack(df_new)
        else:
            print("Column mismatch between existing DataFrame and CSV file!")
    count=+1

df.write_parquet("police_data/compiled_data.parquet")

df = pl.read_parquet("police_data/compiled_data.parquet")
print(df)

# git lfs track "*.parquet"