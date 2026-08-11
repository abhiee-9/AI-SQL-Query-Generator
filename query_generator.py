import os
import re
import sqlparse
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import engine, get_schema

# Load environment variables
load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DEFAULT_ROW_LIMIT = int(os.getenv("DEFAULT_ROW_LIMIT", "200"))

# Statements we will never allow this app to execute. This is a demo /
# read-only query tool, so anything that mutates schema or data is blocked.
_FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "REPLACE", "MERGE", "CALL",
    "EXEC", "EXECUTE", "LOAD_FILE", "INTO OUTFILE", "INTO DUMPFILE",
)

_client = None


def get_client() -> OpenAI:
    """Lazily create the OpenAI client so import doesn't fail without a key."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def clean_sql_output(response_text: str) -> str:
    """Strips markdown fences / prose and returns just the SQL statement."""
    text_ = response_text.strip()

    # Remove ```sql ... ``` or ``` ... ``` fences regardless of exact spacing.
    fence_match = re.search(r"```(?:sql)?\s*(.*?)```", text_, re.DOTALL | re.IGNORECASE)
    if fence_match:
        text_ = fence_match.group(1).strip()

    # If the model added explanation before/after the statement, isolate the
    # first SQL statement (SELECT or WITH ... SELECT), up to the first ';'
    # or the end of the string.
    stmt_match = re.search(
        r"(SELECT|WITH)\b.*?(;|$)", text_, re.DOTALL | re.IGNORECASE
    )
    if stmt_match:
        text_ = stmt_match.group(0).strip()

    if not text_.endswith(";"):
        text_ += ";"

    return text_


def is_safe_select(sql_query: str) -> tuple[bool, str | None]:
    """Only allow read-only SELECT / WITH statements, single statement only."""
    stripped = sql_query.strip().rstrip(";").strip()

    if not stripped:
        return False, "Empty SQL query."

    if ";" in stripped:
        return False, "Multiple statements are not allowed."

    if not re.match(r"^(SELECT|WITH)\b", stripped, re.IGNORECASE):
        return False, "Only SELECT statements are allowed."

    upper = stripped.upper()
    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", upper):
            return False, f"Query contains disallowed keyword: {keyword}"

    return True, None


def validate_sql_query(sql_query: str) -> tuple[bool, str | None]:
    """Validates SQL syntax AND enforces the read-only safety policy."""
    try:
        parsed = sqlparse.parse(sql_query)
        if not parsed or not str(parsed[0]).strip():
            return False, "Invalid SQL syntax."
    except Exception as e:
        return False, f"SQL parse error: {e}"

    return is_safe_select(sql_query)


def _ensure_row_limit(sql_query: str) -> str:
    """Appends a LIMIT clause to SELECT queries that don't already have one,
    so a demo query can't accidentally pull an entire large table."""
    stripped = sql_query.strip().rstrip(";").strip()
    if re.search(r"\bLIMIT\s+\d+\b", stripped, re.IGNORECASE):
        return stripped + ";"
    return f"{stripped} LIMIT {DEFAULT_ROW_LIMIT};"


def generate_sql_query(nl_query: str) -> str | None:
    """Converts natural language query to an optimized, read-only MySQL query."""
    if not nl_query or not nl_query.strip():
        return None

    try:
        schema = get_schema()
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return None

    if not schema:
        print("No schema found — is the database connected and does it have tables?")
        return None

    schema_text = "\n".join(
        f"{table}: {', '.join(columns)}" for table, columns in schema.items()
    )

    prompt = f"""You are an SQL expert. Convert the following natural language
request into a single, optimized, READ-ONLY MySQL SELECT query.

Rules:
- Only ever produce a SELECT (or WITH ... SELECT) statement.
- Never produce INSERT, UPDATE, DELETE, DROP, ALTER, or any other mutating statement.
- Use efficient JOINs instead of nested subqueries where possible.
- Use GROUP BY when aggregation is required.
- Only reference tables/columns that exist in the schema below.
- Return ONLY the SQL query, nothing else — no explanation, no markdown.

Database Schema:
{schema_text}

User Request: {nl_query}

SQL Query:"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a MySQL optimization expert who writes only read-only SELECT queries."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        raw_sql_query = response.choices[0].message.content.strip()
        clean_query = clean_sql_output(raw_sql_query)

        is_valid, error_msg = is_safe_select(clean_query)
        if not is_valid:
            print(f"Generated query rejected by safety check: {error_msg}")
            return None

        return clean_query

    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None


def suggest_index(sql_query: str) -> str:
    """Suggests indexes for the executed SQL query using EXPLAIN."""
    try:
        with engine.connect() as connection:
            explain_query = f"EXPLAIN {sql_query.rstrip(';')}"
            result = connection.execute(text(explain_query))
            execution_plan = result.fetchall()

        tips = []
        for row in execution_plan:
            row_dict = dict(row._mapping)
            if (row_dict.get("key") is None) and row_dict.get("possible_keys") is None:
                tips.append(
                    f"Table '{row_dict.get('table')}': no index used "
                    f"(scanned ~{row_dict.get('rows')} rows) — consider adding an "
                    f"index on the columns used in WHERE/JOIN/ORDER BY."
                )

        if not tips:
            return "Query plan looks reasonably optimized; no obvious missing indexes detected."
        return " ".join(tips)

    except Exception as e:
        return f"Could not generate execution plan: {e}"


def execute_query(sql_query: str):
    """Validates, safety-checks, limits, and executes a SQL query."""
    is_valid, error_msg = validate_sql_query(sql_query)
    if not is_valid:
        print(f"SQL Validation Error: {error_msg}")
        return None

    limited_query = _ensure_row_limit(sql_query)

    try:
        with engine.connect() as connection:
            result = connection.execute(text(limited_query))
            fetched_results = result.fetchall()

        index_suggestion = suggest_index(limited_query)

        return {"results": fetched_results, "optimization_tips": index_suggestion}
    except SQLAlchemyError as e:
        print(f"Database Execution Error: {str(e)}")
        return None


if __name__ == "__main__":
    user_input = input("Enter your natural language query: ")
    sql_query = generate_sql_query(user_input)

    if sql_query:
        print(f"\nGenerated SQL Query:\n{sql_query}")

        execution_results = execute_query(sql_query)
        if execution_results:
            print("\nQuery Results:")
            for row in execution_results["results"]:
                print(row)
            print("\nOptimization Tips:", execution_results["optimization_tips"])
        else:
            print("No results found or error executing query.")
    else:
        print("Failed to generate a valid SQL query.")
