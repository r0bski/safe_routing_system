import polars as pl

df=pl.read_parquet("compiled_data.parquet")
print(df.columns)

crimes=[]
for row in df.rows():
    if row[2] not in crimes:
        crimes.append(row[2])
print(crimes)
