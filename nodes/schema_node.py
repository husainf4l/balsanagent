from typing import Dict, List, Any, Tuple
from tools.db_tools import get_db_schema_and_tables, get_table_definition
from tools.llm_tools import analyze_schema, analyze_columns
import json

def process_schema(input_text: str) -> List[Tuple[str, str, str, str]]:
    """Process schema discovery and analysis."""
    print("\n=== Starting Schema Analysis ===")
    
    # Get all schemas and tables
    print("\n1. Getting all schemas and tables...")
    schemas_and_tables = get_db_schema_and_tables.invoke({})
    print(f"Found schemas: {list(schemas_and_tables.keys())}")
    total_tables = sum(len(tables) for tables in schemas_and_tables.values())
    print(f"Total tables found: {total_tables}")
    
    # Initialize variables for iterative refinement
    max_iterations = 20
    current_iteration = 0
    best_sales_tables = []
    previous_analysis = None
    
    while current_iteration < max_iterations:
        current_iteration += 1
        print(f"\n=== Iteration {current_iteration} of {max_iterations} ===")
        
        # Analyze tables with LLM
        print("\n2. Analyzing tables with LLM...")
        schema_info_str = json.dumps(schemas_and_tables, indent=2)
        llm_analysis = analyze_schema.invoke({"schema_info": schema_info_str, "user_query": previous_analysis or input_text})
        print(f"LLM Analysis: {llm_analysis}")
        previous_analysis = llm_analysis
        
        # Get detailed schema for filtered tables
        print("\n3. Getting detailed schema for filtered tables...")
        sales_tables = []
        for schema, tables in schemas_and_tables.items():
            for table in tables:
                if any(sales_term in table.lower() for sales_term in ['sale', 'transaction', 'order']):
                    print(f"\nAnalyzing table: {schema}.{table}")
                    table_def = get_table_definition.invoke({"schema": schema, "table": table})
                    
                    # Identify best columns with LLM
                    print("4. Identifying best columns with LLM...")
                    table_def_str = json.dumps(table_def, indent=2)
                    column_analysis = analyze_columns.invoke({"table_definition": table_def_str, "user_query": input_text})
                    print(f"Column Analysis: {column_analysis}")
                    
                    # Validate columns
                    print("5. Validating columns...")
                    date_column = None
                    sales_column = None
                    for col in table_def:
                        if col['type'].lower() in ['timestamp', 'date', 'timestamp without time zone']:
                            date_column = col['name']
                            print(f"Found date column: {date_column}")
                        elif col['type'].lower() in ['double precision', 'numeric', 'decimal', 'float', 'int', 'integer'] and any(sales_term in col['name'].lower() for sales_term in ['sale', 'amount', 'total', 'price']):
                            sales_column = col['name']
                            print(f"Found sales column: {sales_column}")
                    
                    if date_column and sales_column:
                        print(f"✓ Valid table found: {schema}.{table}")
                        sales_tables.append((schema, table, date_column, sales_column))
                    else:
                        print(f"✗ Table {schema}.{table} rejected - missing required columns")
        
        # Check if we found better tables in this iteration
        print(f"\nFound {len(sales_tables)} valid sales tables in this iteration")
        if sales_tables and (not best_sales_tables or len(sales_tables) > len(best_sales_tables)):
            print("New best set of tables found!")
            best_sales_tables = sales_tables
        elif best_sales_tables and len(sales_tables) == len(best_sales_tables):
            print("Converged on same number of tables - stopping iterations")
            break
    
    return best_sales_tables 