import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity

# Paths
input_file = "../data/processed/cleaned_data.csv"
output_dir = "../data/processed"

os.makedirs(output_dir, exist_ok=True)

# Load cleaned data
df = pd.read_csv(input_file)
df["StockCode"] = df["StockCode"].astype(str)

print("Loaded cleaned data:", df.shape)

# Keep only needed columns
df = df[["CustomerID", "StockCode", "Description", "Quantity"]]

# Group by customer and product
grouped_df = df.groupby(["CustomerID", "StockCode"], as_index=False)["Quantity"].sum()

print("Grouped data shape:", grouped_df.shape)

# Create customer-item matrix
customer_item_matrix = grouped_df.pivot_table(
    index="CustomerID",
    columns="StockCode",
    values="Quantity",
    fill_value=0
)

print("Customer-item matrix shape:", customer_item_matrix.shape)

# Save customer-item matrix
customer_item_matrix.to_csv(f"{output_dir}/customer_item_matrix.csv")

# Transpose matrix for item-item similarity
item_matrix = customer_item_matrix.T

# Compute cosine similarity
similarity = cosine_similarity(item_matrix)

# Create similarity dataframe
item_similarity_df = pd.DataFrame(
    similarity,
    index=item_matrix.index,
    columns=item_matrix.index
)

# Save item similarity
item_similarity_df.to_csv(f"{output_dir}/item_similarity.csv")

print("Item similarity matrix shape:", item_similarity_df.shape)

# Popular products fallback
popular_products = (
    df.groupby(["StockCode", "Description"], as_index=False)["Quantity"]
    .sum()
    .sort_values(by="Quantity", ascending=False)
)

popular_products.to_csv(f"{output_dir}/popular_products.csv", index=False)

print("Popular products shape:", popular_products.shape)

print("\nTop 10 popular products:")
print(popular_products.head(10))

print("\nFiles saved:")
print("- customer_item_matrix.csv")
print("- item_similarity.csv")
print("- popular_products.csv")