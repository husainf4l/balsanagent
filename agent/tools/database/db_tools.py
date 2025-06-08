from typing import Dict, List, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import json

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

# Initialize LLM for analysis tools
llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

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
def get_table_definition(schema_name: str, table: str) -> List[Dict[str, Any]]:
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
            WHERE table_schema = '{schema_name}'
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

@tool
def analyze_schema(schema_info: str, user_query: str) -> str:
    """Analyze the provided schema information and user query, and return suggestions for relevant tables or columns."""
    prompt = f"""
    You are a database expert. Given the following schema information:
    {schema_info}
    And the user query: "{user_query}"
    Suggest the most relevant tables and columns to answer the query. Explain your reasoning.
    """
    response = llm.invoke(prompt)
    return response.content.strip()

@tool
def analyze_columns(table_definition: str, user_query: str) -> str:
    """Analyze the provided table definition and user query, and return suggestions for relevant columns (e.g., date, sales amount)."""
    try:
        # Parse the table definition string back to a list of dictionaries
        columns = json.loads(table_definition)
        
        # Create a more structured prompt
        prompt = f"""
        You are a database expert. Given the following table columns:
        {json.dumps(columns, indent=2)}
        
        And the user query: "{user_query}"
        
        Please identify:
        1. The best column for dates (look for timestamp, date, or datetime types)
        2. The best column for sales amounts (look for numeric types with names containing 'sale', 'amount', 'total', or 'price')
        
        For each column you identify, explain why it's the best choice.
        If you can't find suitable columns, explain why.
        """
        
        response = llm.invoke(prompt)
        return response.content.strip()
    except json.JSONDecodeError:
        return "Error: Invalid table definition format. Please provide a valid JSON string."
    except Exception as e:
        return f"Error analyzing columns: {str(e)}"