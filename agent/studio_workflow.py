# LangGraph Studio compatible workflow
import logging
import os
from typing import Dict, List, Any, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent
from langchain.tools import Tool
from .tools.database import (
    get_db_schema_and_tables, 
    get_table_definition, 
    execute_sql_query,
    analyze_schema, 
    analyze_columns,
    save_summary
)
from .tools.fraud_analysis import detect_suspicious_transactions

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
6. Use detect_suspicious_transactions to analyze a table for potentially suspicious (fraudulent) transactions using multiple rules.

Always:
- Check for data quality issues (missing values, zeros, etc.)
- Provide period-specific comparisons when requested
- Include actionable business advice
- Add disclaimers for prototype data
- Respond in the same language as the user's query
- Maintain context from previous conversations
- Reference previous insights when relevant

IMPORTANT: When users respond with generic confirmations like "ok", "yes", "proceed", "go ahead", or similar:
- Look at the previous conversation to see what analysis options you offered
- Choose the FIRST or MOST RELEVANT option you suggested and execute it automatically
- If you previously suggested "identifying top customers by sales volume", do that analysis
- If you suggested multiple options, pick the most commonly requested business insight
- Don't ask for clarification again - take action based on context

Available tools:
- get_db_schema_and_tables: Get all schemas and tables
- get_table_definition: Get column definitions for a specific table
- analyze_schema: Analyze schema to find relevant tables
- analyze_columns: Identify best columns for analysis
- execute_sql_query: Run SQL queries
- save_summary: Save insights to the database
- detect_suspicious_transactions: Analyze a table for potentially suspicious (fraudulent) transactions using multiple rules.

Please help the user analyze their data and provide insights.
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4-1106-preview",
    temperature=0,
    max_tokens=4000  
)

# Initialize tools
tools = [
    get_db_schema_and_tables,
    get_table_definition,
    execute_sql_query,
    analyze_schema,
    analyze_columns,
    save_summary,
    Tool(
        name="detect_suspicious_transactions",
        func=lambda table, amount_threshold=100000.0: detect_suspicious_transactions(
            execute_sql_query, table, amount_threshold
        ),
        description="Analyze a table for potentially suspicious (fraudulent) transactions using multiple rules. Parameters: table (str), amount_threshold (float, optional)."
    )
]

# Create the agent without custom checkpointer (LangGraph Studio handles persistence)
graph = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT
)
