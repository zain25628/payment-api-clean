# Refactored by Copilot
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Single engine used by the application
engine = create_engine(settings.DATABASE_URL, future=True)

# Register a SQLite-compatible "now()" SQL function so existing
# DEFAULT now() in schemas works without errors when using SQLite.
if engine.url.get_backend_name() == "sqlite":
    @event.listens_for(engine, "connect")
    def _sqlite_register_now_function(dbapi_connection, connection_record):
        # sqlite3 connection: register a SQL function named "now"
        # that returns UTC timestamp as text.
        def _now():
            return datetime.utcnow().isoformat(" ")

        # dbapi_connection is a sqlite3.Connection
        dbapi_connection.create_function("now", 0, _now)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
