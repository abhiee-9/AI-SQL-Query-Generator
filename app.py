from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from query_generator import generate_sql_query, execute_query

app = FastAPI(
    title="QueryZen API",
    description="AI-powered natural language to SQL query generator",
    version="1.0.0",
)

# Allow the Streamlit frontend (and local tools) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


@app.get("/")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "QueryZen API"}


@app.post("/generate_sql/")
async def generate_sql(request: QueryRequest):
    """Generate a read-only SQL query from natural language input."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty")

    try:
        sql_query = generate_sql_query(request.query)
    except RuntimeError as e:
        # e.g. missing OPENAI_API_KEY
        raise HTTPException(status_code=500, detail=str(e))

    if not sql_query:
        raise HTTPException(
            status_code=422,
            detail="Could not generate a valid, safe SQL query for that request.",
        )
    return {"sql_query": sql_query}


@app.post("/execute_sql/")
async def execute_sql(request: QueryRequest):
    """Execute a given (read-only) SQL query and return results."""
    sql_query = request.query
    if not sql_query or not sql_query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty")

    try:
        results = execute_query(sql_query)

        if results is None:
            raise HTTPException(
                status_code=400,
                detail="Query failed validation or execution. Only read-only "
                       "SELECT statements are allowed.",
            )

        serialized_results = [dict(row._mapping) for row in results["results"]]

        return {
            "results": serialized_results,
            "optimization_tips": results["optimization_tips"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
