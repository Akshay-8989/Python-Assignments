from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:komisan89@localhost:5433/ecommerce_reco"
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE transactions, products, customers RESTART IDENTITY CASCADE"))
    print("truncate done")