import pandas as pd
import json
import time
from kafka import KafkaProducer

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8")
)

# Load cleaned data
df = pd.read_csv("../data/processed/cleaned_data.csv")

# Convert rows to messages
for _, row in df.iterrows():
    message = {
        "InvoiceNo": str(row["InvoiceNo"]),
        "StockCode": str(row["StockCode"]),
        "Description": str(row["Description"]),
        "Quantity": int(row["Quantity"]),
        "InvoiceDate": str(row["InvoiceDate"]),
        "UnitPrice": float(row["UnitPrice"]),
        "CustomerID": int(row["CustomerID"]),
        "Country": str(row["Country"]),
        "TotalAmount": float(row["TotalAmount"])
    }

    producer.send("transactions_topic", value=message)
    print("Sent:", message)

    time.sleep(0.01)   # small delay to simulate streaming

producer.flush()
print("All messages sent successfully.")