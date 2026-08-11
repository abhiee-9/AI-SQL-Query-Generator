import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database credentials
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

if not MYSQL_DATABASE:
    raise RuntimeError(
        "MYSQL_DATABASE is not set. Copy .env.example to .env and fill in "
        "your database credentials."
    )

# Create MySQL connection URL
DATABASE_URL = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# Create SQLAlchemy engine (pool_pre_ping avoids stale-connection errors)
engine = create_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True)


def test_connection() -> bool:
    """Quick sanity check that the DB is reachable. Returns True/False."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE();"))
            print(f"Connected to: {result.fetchone()[0]}")
        return True
    except Exception as e:
        print(f"Error connecting to MySQL: {e}")
        return False


def get_schema() -> dict:
    """Returns {table_name: ['col (type)', ...]} for the configured database."""
    query = """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = :database
    ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """
    with engine.connect() as connection:
        result = connection.execute(text(query), {"database": MYSQL_DATABASE})
        schema_info = result.fetchall()

    schema_dict: dict = {}
    for table, column, dtype in schema_info:
        schema_dict.setdefault(table, []).append(f"{column} ({dtype})")

    return schema_dict


# Run connection test
if __name__ == "__main__":
    test_connection()
