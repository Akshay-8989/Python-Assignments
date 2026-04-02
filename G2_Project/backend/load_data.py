<<<<<<< HEAD
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "processed" / "cleaned_data.csv"

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Load cleaned data
df = pd.read_csv(DATA_FILE)

# Fix data types
df["CustomerID"] = df["CustomerID"].astype(int)
df["StockCode"] = df["StockCode"].astype(str)
df["InvoiceNo"] = df["InvoiceNo"].astype(str)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# Prepare customers
customers_df = (
    df[["CustomerID", "Country"]]
    .dropna()
    .groupby("CustomerID", as_index=False)
    .first()
)
customers_df.columns = ["customer_id", "country"]

# Prepare products
products_df = (
    df[["StockCode", "Description", "UnitPrice"]]
    .dropna(subset=["StockCode"])
    .drop_duplicates(subset=["StockCode"])
)
products_df.columns = ["stock_code", "description", "unit_price"]

# Prepare transactions
transactions_df = df[
    [
        "InvoiceNo",
        "CustomerID",
        "StockCode",
        "Description",
        "Quantity",
        "UnitPrice",
        "InvoiceDate",
        "Country",
    ]
].copy()

transactions_df.columns = [
    "invoice_no",
    "customer_id",
    "stock_code",
    "description",
    "quantity",
    "unit_price",
    "invoice_date",
    "country",
]

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE transactions, products, customers RESTART IDENTITY CASCADE"))

print("Old data cleared.")

customers_df.to_sql("customers", con=engine, if_exists="append", index=False)
print("Customers loaded:", customers_df.shape)

products_df.to_sql("products", con=engine, if_exists="append", index=False)
print("Products loaded:", products_df.shape)

transactions_df.to_sql("transactions", con=engine, if_exists="append", index=False)
print("Transactions loaded:", transactions_df.shape)

=======
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "processed" / "cleaned_data.csv"

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Load cleaned data
df = pd.read_csv(DATA_FILE)

# Fix data types
df["CustomerID"] = df["CustomerID"].astype(int)
df["StockCode"] = df["StockCode"].astype(str)
df["InvoiceNo"] = df["InvoiceNo"].astype(str)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

# Prepare customers
customers_df = (
    df[["CustomerID", "Country"]]
    .dropna()
    .groupby("CustomerID", as_index=False)
    .first()
)
customers_df.columns = ["customer_id", "country"]

# Prepare products
products_df = (
    df[["StockCode", "Description", "UnitPrice"]]
    .dropna(subset=["StockCode"])
    .drop_duplicates(subset=["StockCode"])
)
products_df.columns = ["stock_code", "description", "unit_price"]

# Prepare transactions
transactions_df = df[
    [
        "InvoiceNo",
        "CustomerID",
        "StockCode",
        "Description",
        "Quantity",
        "UnitPrice",
        "InvoiceDate",
        "Country",
    ]
].copy()

transactions_df.columns = [
    "invoice_no",
    "customer_id",
    "stock_code",
    "description",
    "quantity",
    "unit_price",
    "invoice_date",
    "country",
]

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE transactions, products, customers RESTART IDENTITY CASCADE"))

print("Old data cleared.")

customers_df.to_sql("customers", con=engine, if_exists="append", index=False)
print("Customers loaded:", customers_df.shape)

products_df.to_sql("products", con=engine, if_exists="append", index=False)
print("Products loaded:", products_df.shape)

transactions_df.to_sql("transactions", con=engine, if_exists="append", index=False)
print("Transactions loaded:", transactions_df.shape)

>>>>>>> 078f103c00d85cbbec5ede50581083ac1663ff12
print("All data inserted successfully.")