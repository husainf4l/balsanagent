from langchain.tools import tool
from langchain_openai import ChatOpenAI
import os
import json

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

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