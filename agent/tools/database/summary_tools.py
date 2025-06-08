from typing import Dict, Any
from langchain.tools import tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

# Debug: Print environment variables
print("Environment variables loaded in summary_tools:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

# Initialize database connection
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(db_url)

@tool
def save_summary(summary: str, query: str) -> Dict[str, Any]:
    """Save a summary of the analysis results to the database."""
    try:
        with engine.connect() as conn:
            # Create summaries table if it doesn't exist
            create_table_query = text("""
            CREATE TABLE IF NOT EXISTS analysis_summaries (
                id SERIAL PRIMARY KEY,
                summary TEXT,
                query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.execute(create_table_query)
            
            # Insert the summary
            insert_query = text("""
            INSERT INTO analysis_summaries (summary, query)
            VALUES (:summary, :query)
            RETURNING id
            """)
            result = conn.execute(insert_query, {"summary": summary, "query": query}).fetchone()
            
            return {
                "success": True,
                "id": result[0],
                "message": "Summary saved successfully"
            }
    except Exception as e:
        print(f"Error saving summary: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 