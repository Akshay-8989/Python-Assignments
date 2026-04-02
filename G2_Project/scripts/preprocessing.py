import pandas as pd

# File paths
input_file = "../data/raw/G2_data.csv"
output_file = "../data/processed/cleaned_data.csv"

# Load dataset
df = pd.read_csv(input_file, encoding="latin1")

print("Original shape:", df.shape)
print("\nColumns:")
print(df.columns)

# Rename columns properly if needed
df.columns = df.columns.str.strip()

# Drop rows where CustomerID is missing
df = df.dropna(subset=["CustomerID"])

# Remove cancelled invoices (InvoiceNo starting with C)
df["InvoiceNo"] = df["InvoiceNo"].astype(str)
df = df[~df["InvoiceNo"].str.startswith("C")]

# Keep only positive Quantity and UnitPrice
df = df[df["Quantity"] > 0]
df = df[df["UnitPrice"] > 0]

# Drop duplicate rows
df = df.drop_duplicates()

# Convert CustomerID to int
df["CustomerID"] = df["CustomerID"].astype(int)

# Convert InvoiceDate to datetime
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

# Drop rows where InvoiceDate conversion failed
df = df.dropna(subset=["InvoiceDate"])

# Create TotalAmount column
df["TotalAmount"] = df["Quantity"] * df["UnitPrice"]

# Save cleaned data
df.to_csv(output_file, index=False)

print("\nCleaned shape:", df.shape)
print("\nMissing values:")
print(df.isnull().sum())

print("\nFirst 5 rows:")
print(df.head())

print(f"\nCleaned data saved to: {output_file}")