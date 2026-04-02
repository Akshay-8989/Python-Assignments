<<<<<<< HEAD
import pandas as pd

# Load files
customer_item_matrix = pd.read_csv(
    "../data/processed/customer_item_matrix.csv",
    index_col=0
)

item_similarity = pd.read_csv(
    "../data/processed/item_similarity.csv",
    index_col=0,
    low_memory=False
)

popular_products = pd.read_csv("../data/processed/popular_products.csv")

# Make StockCode consistent everywhere
customer_item_matrix.columns = customer_item_matrix.columns.astype(str)
item_similarity.index = item_similarity.index.astype(str)
item_similarity.columns = item_similarity.columns.astype(str)
popular_products["StockCode"] = popular_products["StockCode"].astype(str)


def get_recommendations(customer_id, top_n=10):
    customer_id = int(customer_id)

    # If customer not found, return popular products
    if customer_id not in customer_item_matrix.index:
        print(f"Customer {customer_id} not found. Showing popular products.")
        return popular_products.head(top_n)

    # Products already bought by customer
    purchased_products = customer_item_matrix.loc[customer_id]
    purchased_products = purchased_products[purchased_products > 0].index.tolist()

    if len(purchased_products) == 0:
        print(f"Customer {customer_id} has no purchase history. Showing popular products.")
        return popular_products.head(top_n)

    recommendation_scores = {}

    # For each purchased product, get similar products
    for product in purchased_products:
        if product in item_similarity.index:
            similar_items = item_similarity.loc[product].sort_values(ascending=False)

            for similar_product, score in similar_items.items():
                if similar_product != product:
                    if similar_product not in recommendation_scores:
                        recommendation_scores[similar_product] = 0
                    recommendation_scores[similar_product] += score

    # Remove already purchased products
    for product in purchased_products:
        if product in recommendation_scores:
            del recommendation_scores[product]

    # Convert to dataframe
    recommendations_df = pd.DataFrame(
        recommendation_scores.items(),
        columns=["StockCode", "Score"]
    )

    if recommendations_df.empty:
        print("No personalized recommendations found. Showing popular products.")
        return popular_products.head(top_n)

    recommendations_df["StockCode"] = recommendations_df["StockCode"].astype(str)

    # Sort by score
    recommendations_df = recommendations_df.sort_values(by="Score", ascending=False)

    # Merge with product descriptions
    product_info = popular_products[["StockCode", "Description"]].drop_duplicates()
    recommendations_df = recommendations_df.merge(product_info, on="StockCode", how="left")

    return recommendations_df.head(top_n)[["StockCode", "Description", "Score"]]


if __name__ == "__main__":
    customer_id = input("Enter CustomerID: ")
    recommendations = get_recommendations(customer_id, top_n=10)

    print("\nRecommended products:")
=======
import pandas as pd

# Load files
customer_item_matrix = pd.read_csv(
    "../data/processed/customer_item_matrix.csv",
    index_col=0
)

item_similarity = pd.read_csv(
    "../data/processed/item_similarity.csv",
    index_col=0,
    low_memory=False
)

popular_products = pd.read_csv("../data/processed/popular_products.csv")

# Make StockCode consistent everywhere
customer_item_matrix.columns = customer_item_matrix.columns.astype(str)
item_similarity.index = item_similarity.index.astype(str)
item_similarity.columns = item_similarity.columns.astype(str)
popular_products["StockCode"] = popular_products["StockCode"].astype(str)


def get_recommendations(customer_id, top_n=10):
    customer_id = int(customer_id)

    # If customer not found, return popular products
    if customer_id not in customer_item_matrix.index:
        print(f"Customer {customer_id} not found. Showing popular products.")
        return popular_products.head(top_n)

    # Products already bought by customer
    purchased_products = customer_item_matrix.loc[customer_id]
    purchased_products = purchased_products[purchased_products > 0].index.tolist()

    if len(purchased_products) == 0:
        print(f"Customer {customer_id} has no purchase history. Showing popular products.")
        return popular_products.head(top_n)

    recommendation_scores = {}

    # For each purchased product, get similar products
    for product in purchased_products:
        if product in item_similarity.index:
            similar_items = item_similarity.loc[product].sort_values(ascending=False)

            for similar_product, score in similar_items.items():
                if similar_product != product:
                    if similar_product not in recommendation_scores:
                        recommendation_scores[similar_product] = 0
                    recommendation_scores[similar_product] += score

    # Remove already purchased products
    for product in purchased_products:
        if product in recommendation_scores:
            del recommendation_scores[product]

    # Convert to dataframe
    recommendations_df = pd.DataFrame(
        recommendation_scores.items(),
        columns=["StockCode", "Score"]
    )

    if recommendations_df.empty:
        print("No personalized recommendations found. Showing popular products.")
        return popular_products.head(top_n)

    recommendations_df["StockCode"] = recommendations_df["StockCode"].astype(str)

    # Sort by score
    recommendations_df = recommendations_df.sort_values(by="Score", ascending=False)

    # Merge with product descriptions
    product_info = popular_products[["StockCode", "Description"]].drop_duplicates()
    recommendations_df = recommendations_df.merge(product_info, on="StockCode", how="left")

    return recommendations_df.head(top_n)[["StockCode", "Description", "Score"]]


if __name__ == "__main__":
    customer_id = input("Enter CustomerID: ")
    recommendations = get_recommendations(customer_id, top_n=10)

    print("\nRecommended products:")
>>>>>>> 078f103c00d85cbbec5ede50581083ac1663ff12
    print(recommendations)