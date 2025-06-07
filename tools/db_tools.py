from typing import Dict, List, Any
from langchain.tools import tool
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(override=True)

# Debug: Print environment variables
print("Environment variables loaded:")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

# Initialize database connection
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(db_url)

@tool
def get_db_schema_and_tables() -> Dict[str, List[str]]:
    """Get all schemas and their tables from the database."""
    try:
        with engine.connect() as conn:
            # Get all schemas
            schemas_query = text("""
            SELECT DISTINCT table_schema 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            """)
            schemas = conn.execute(schemas_query).fetchall()
            
            # Get tables for each schema
            result = {}
            for schema in schemas:
                tables_query = text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema[0]}'
                """)
                tables = conn.execute(tables_query).fetchall()
                result[schema[0]] = [table[0] for table in tables]
            
            return result
    except Exception as e:
        print(f"Error getting schema and tables: {str(e)}")
        return {}

@tool
def get_table_definition(schema: str, table: str) -> List[Dict[str, Any]]:
    """Get the definition of a specific table including column names and types."""
    try:
        with engine.connect() as conn:
            query = text(f"""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = '{schema}'
            AND table_name = '{table}'
            ORDER BY ordinal_position
            """)
            columns = conn.execute(query).fetchall()
            
            return [
                {
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2],
                    "default": col[3]
                }
                for col in columns
            ]
    except Exception as e:
        print(f"Error getting table definition: {str(e)}")
        return []

@tool
def execute_sql_query(query: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return the results."""
    try:
        with engine.connect() as conn:
            # Execute the query
            result = conn.execute(text(query))
            
            # Get column names from the result
            columns = result.keys()
            
            # Convert rows to dictionaries
            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    # Convert any numeric types to float for JSON serialization
                    value = row[i]
                    if isinstance(value, (int, float)):
                        value = float(value)
                    row_dict[col] = value
                rows.append(row_dict)
            
            return rows
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        return [] 