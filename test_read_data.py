import polars as pl

df=pl.read_parquet("compiled_data.parquet")
print(df.columns)