import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

customer_item_matrix = pd.read_csv(PROCESSED_DIR / "customer_item_matrix.csv", index_col=0)
item_similarity = pd.read_csv(PROCESSED_DIR / "item_similarity.csv", index_col=0, low_memory=False)
popular_products = pd.read_csv(PROCESSED_DIR / "popular_products.csv")

customer_item_matrix.columns = customer_item_matrix.columns.astype(str)
customer_item_matrix.index = customer_item_matrix.index.astype(int)

item_similarity.index = item_similarity.index.astype(str)
item_similarity.columns = item_similarity.columns.astype(str)

popular_products["StockCode"] = popular_products["StockCode"].astype(str)


def get_recommendations(customer_id, top_n=10):
    customer_id = int(customer_id)

    if customer_id not in customer_item_matrix.index:
        return popular_products.head(top_n).to_dict(orient="records")

    purchased_products = customer_item_matrix.loc[customer_id]
    purchased_products = purchased_products[purchased_products > 0].index.tolist()

    if len(purchased_products) == 0:
        return popular_products.head(top_n).to_dict(orient="records")

    recommendation_scores = {}

    for product in purchased_products:
        if product in item_similarity.index:
            similar_items = item_similarity.loc[product].sort_values(ascending=False)

            for similar_product, score in similar_items.items():
                if similar_product != product:
                    recommendation_scores[similar_product] = recommendation_scores.get(similar_product, 0) + score

    for product in purchased_products:
        recommendation_scores.pop(product, None)

    recommendations_df = pd.DataFrame(
        recommendation_scores.items(),
        columns=["StockCode", "Score"]
    )

    if recommendations_df.empty:
        return popular_products.head(top_n).to_dict(orient="records")

    recommendations_df["StockCode"] = recommendations_df["StockCode"].astype(str)
    recommendations_df = recommendations_df.sort_values(by="Score", ascending=False)

    product_info = popular_products[["StockCode", "Description"]].drop_duplicates()
    recommendations_df = recommendations_df.merge(product_info, on="StockCode", how="left")

    return recommendations_df.head(top_n)[["StockCode", "Description", "Score"]].to_dict(orient="records")