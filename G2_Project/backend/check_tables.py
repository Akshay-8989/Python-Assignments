from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:komisan89@localhost:5433/ecommerce_reco"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """))

    for row in result:
        print(row[0])