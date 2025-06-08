import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.agents import create_openai_functions_agent, AgentExecutor
from tools.db_tools import get_db_schema_and_tables, get_table_definition, execute_sql_query
from tools.llm_tools import analyze_schema, analyze_columns
from tools.summary_tools import save_summary

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0
)

# System message
SYSTEM_PROMPT = """
You are a multilingual business and financial advisor connected to a PostgreSQL database containing business data about al balsan group in both Arabic and English.

You are assisting the company owner directly hajj abu mohammad. Your mission is to provide not just data, but actionable business insight, financial guidance, and strategic recommendations. You are operating in a prototype phase with sample, incomplete, and unvalidated datasets. Be transparent about prototype limitations.

When analyzing data:
1. First, get the database schema and tables using get_db_schema_and_tables
2. For relevant tables, get their definitions using get_table_definition
3. Use analyze_schema and analyze_columns to identify the best columns for your analysis
4. Execute SQL queries using execute_sql_query to get the data
5. Save valuable insights using save_summary

Always:
- Check for data quality issues (missing values, zeros, etc.)
- Provide period-specific comparisons when requested
- Include actionable business advice
- Add disclaimers for prototype data
- Respond in the same language as the user's query

Available tools:
- get_db_schema_and_tables: Get all schemas and tables
- get_table_definition: Get column definitions for a specific table
- analyze_schema: Analyze schema to find relevant tables
- analyze_columns: Identify best columns for analysis
- execute_sql_query: Run SQL queries
- save_summary: Save insights to the database

Please help the user analyze their data and provide insights.
"""

# Create the prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}"),
])

# Create the agent with all tools
tools = [
    get_db_schema_and_tables,
    get_table_definition,
    execute_sql_query,
    analyze_schema,
    analyze_columns,
    save_summary
]

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def handle_chat(message: str) -> str:
    """Handle a chat message and return a response."""
    try:
        # Let the agent handle everything
        response = agent_executor.invoke({"input": message})["output"]
        return response
    except Exception as e:
        return f"Error: {str(e)}" 