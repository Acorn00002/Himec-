from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added after the first release. There is no Alembic in this project (SQLite dev
# DB), and SQLAlchemy's create_all never ALTERs an existing table, so we additively patch
# in any missing column on startup. Existing rows get the SQL default / NULL.
_ADDITIVE_COLUMNS: dict[str, dict[str, str]] = {
    "issues": {
        "disposition": "VARCHAR(20) DEFAULT 'open'",
        "review_comment": "TEXT",
        "reviewed_by": "VARCHAR(100)",
        "reviewed_at": "DATETIME",
    },
}


def run_light_migrations() -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue  # create_all will build it with every column
            present = {col["name"] for col in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in present:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
