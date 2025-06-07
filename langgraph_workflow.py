import os
from typing import Dict, List, Tuple, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import tool
import re
from nodes.schema_node import process_schema
from nodes.analysis_node import process_analysis
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
- Always check for data quality issues (missing values, zeros, etc.)
- Provide period-specific comparisons when requested
- Include actionable business advice
- Save valuable insights to the summaries table
- Add disclaimers for prototype data
- Respond in the same language as the user's query

Please help the user analyze their data and provide insights.
"""

# Create the prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}"),
])

def process_input(input_text: str) -> str:
    """Process user input and return a response."""
    try:
        # print("\n=== Starting Workflow Analysis ===")
        # print(f"Input query: {input_text}")
        
        # # Detect language
        is_arabic = any(ord(c) > 127 for c in input_text)
        # print(f"Language detected: {'Arabic' if is_arabic else 'English'}")
        
        # Extract years and periods from query
        years = re.findall(r'20\d{2}', input_text)
        periods = re.findall(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)(?:\s*-\s*(?:January|February|March|April|May|June|July|August|September|October|November|December))?', input_text, re.IGNORECASE)
        # print(f"Extracted years: {years}")
        # print(f"Extracted periods: {periods}")
        
        # Process schema discovery and analysis
        sales_tables = process_schema(input_text)
        
        if not sales_tables:
            print("\n❌ No suitable sales tables found after all iterations")
            return "No suitable sales tables found in the database after multiple attempts."
        
        # Process analysis
        return process_analysis(sales_tables, years, periods)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return f"Error processing input: {str(e)}"

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
        # Process the input using our custom logic
        response = process_input(message)
        
        # If our custom logic doesn't find a suitable response, use the agent
        if "Could not find suitable columns" in response or "No sales-related tables" in response:
            response = agent_executor.invoke({"input": message})["output"]
        
        return response
    except Exception as e:
        return f"Error: {str(e)}" 