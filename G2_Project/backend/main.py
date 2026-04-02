from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from db import engine
from recommender import get_recommendations

app = FastAPI(title="E-commerce Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "E-commerce Recommendation API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/recommend/{customer_id}")
def recommend(customer_id: int, top_n: int = 10):
    recommendations = get_recommendations(customer_id, top_n)
    return {
        "customer_id": customer_id,
        "recommendations": recommendations
    }


@app.get("/customer/{customer_id}/history")
def customer_history(customer_id: int):
    query = text("""
        SELECT invoice_no, stock_code, description, quantity, unit_price, invoice_date
        FROM transactions
        WHERE customer_id = :customer_id
        ORDER BY invoice_date DESC
        LIMIT 20
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"customer_id": customer_id})
        rows = [dict(row._mapping) for row in result]

    return {
        "customer_id": customer_id,
        "history": rows
    }


@app.get("/popular")
def popular_products(limit: int = 10):
    query = text("""
        SELECT stock_code, description, unit_price
        FROM products
        LIMIT :limit
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"limit": limit})
        rows = [dict(row._mapping) for row in result]

    return {"popular_products": rows}