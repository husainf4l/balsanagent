# Agent Structure Documentation

## Overview

The agent has been reorganized into a more logical and maintainable structure. All related tools are now grouped together based on their functionality.

## New Structure

```
aqlon/
├── agent/                              # Agent tools and components
│   └── tools/                          # Tools package
│       ├── __init__.py                 # Tools package exports
│       └── database/                   # Database-related tools
│           ├── __init__.py             # Database tools exports
│           ├── db_tools.py             # Direct database operations
│           ├── llm_tools.py            # LLM-powered database analysis
│           └── summary_tools.py        # Database insights storage
├── workflows/                          # Main workflow package
│   ├── __init__.py                     # Workflow package exports
│   └── langgraph_workflow.py           # Core workflow and chat management
├── tests/                              # Test files and interfaces
│   ├── __init__.py                     # Tests package exports
│   ├── test_chat.py                    # Interactive chat interface
│   ├── test_components.py              # Component testing
│   └── test_db_copy.py                 # Database copy testing
├── utils/                              # Utility scripts
│   ├── __init__.py                     # Utils package exports
│   ├── check_env.py                    # Environment validation
│   └── copy_database.py               # Database utilities
├── requirements.txt                    # Python dependencies
└── others/                             # Additional documentation
    └── README.md
```

## Tool Organization Logic

### Database Tools Package (`agent/tools/database/`)

All database-related functionality is now grouped together:

1. **`db_tools.py`** - Core database operations:

   - `get_db_schema_and_tables()` - Schema discovery
   - `get_table_definition()` - Table structure analysis
   - `execute_sql_query()` - Safe SQL execution

2. **`llm_tools.py`** - LLM-powered database analysis:

   - `analyze_schema()` - AI-powered schema analysis
   - `analyze_columns()` - AI-powered column identification
   - Uses OpenAI GPT models to understand database structure

3. **`summary_tools.py`** - Insights storage:
   - `save_summary()` - Store analysis results back to database
   - Creates and manages the `analysis_summaries` table

## Key Benefits

1. **Logical Grouping**: LLM tools and database tools work together for database analysis
2. **Clear Separation**: Database-specific functionality is isolated
3. **Easy Imports**: Clean import paths with proper `__init__.py` files
4. **Maintainability**: Related code is co-located
5. **Scalability**: Easy to add new tool categories (e.g., `agent/tools/reporting/`)

## Import Patterns

### From the workflow:

```python
from agent.tools.database import (
    get_db_schema_and_tables,
    get_table_definition,
    execute_sql_query,
    analyze_schema,
    analyze_columns,
    save_summary
)
```

### From external files:

```python
from agent.tools.database import get_db_schema_and_tables
# or
from workflows.langgraph_workflow import handle_chat
```

## Usage

The reorganization maintains the external API while improving code organization. The chat interface can now be run from the tests directory:

```bash
python tests/test_chat.py
```

All tools are still available to the LangGraph agent and function identically to before, but now with better organization and maintainability.
