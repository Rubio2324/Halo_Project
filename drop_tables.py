from sqlmodel import SQLModel
from sqlalchemy import text
from utils.db import engine

def drop_and_create_tables():
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS player CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS team CASCADE;"))
        # recreate tables within the same transaction to ensure it's synced
        SQLModel.metadata.create_all(conn)

    print("Tablas player y team borradas y recreadas correctamente.")

if __name__ == "__main__":
    drop_and_create_tables()
