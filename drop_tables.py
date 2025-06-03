from sqlmodel import SQLModel
from sqlalchemy import text
from utils.db import engine

def drop_and_create_tables():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS player CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS team CASCADE;"))
        conn.commit()

    SQLModel.metadata.create_all(engine)
    print("Tablas player y team borradas y recreadas correctamente.")

if __name__ == "__main__":
    drop_and_create_tables()
