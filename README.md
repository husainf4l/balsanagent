# Al Balsan Group Business Advisor

This is a LangGraph implementation of a multilingual business and financial advisor for Al Balsan Group. The system connects to a PostgreSQL database and provides business insights in both Arabic and English.

## Features

- Multilingual support (Arabic and English)
- Database schema exploration
- SQL query execution
- Table definition retrieval
- Chat history persistence in PostgreSQL
- Business insights and recommendations

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key

### Installation

1. Clone the repository:

```bash
git clone git@github.com:husainf4l/balsanagent.git
cd balsanagent
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your actual values:

```
OPENAI_API_KEY=your_openai_api_key_here
POSTGRES_DB=balsanaiagent
POSTGRES_USER=husain
POSTGRES_PASSWORD=your_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
LOG_LEVEL=INFO
DEBUG_MODE=false
```

4. Database Setup:
   Make sure your PostgreSQL database is running and accessible with the credentials provided in the environment variables.

5. Test the setup:

```bash
python check_env.py
```

## Project Structure

```
balsanagent/
├── langgraph_workflow.py     # Main workflow implementation
├── check_env.py             # Environment validation script
├── test_workflow.py         # Workflow tests
├── test_components.py       # Component tests
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── nodes/                  # LangGraph nodes
│   ├── __init__.py
│   ├── schema_node.py      # Database schema discovery
│   └── analysis_node.py    # Data analysis logic
└── tools/                  # LangChain tools
    ├── __init__.py
    ├── db_tools.py         # Database operations
    ├── llm_tools.py        # LLM-based analysis
    └── summary_tools.py    # Insights management
```

## Usage

The main entry point is the `handle_chat` function in `langgraph_workflow.py`:

```python
from langgraph_workflow import handle_chat

# Handle a chat message
response = handle_chat("What are our top selling products this month?")
print(response)

# Arabic example
response = handle_chat("ما هي أفضل المنتجات مبيعاً هذا الشهر؟")
print(response)
```

## API Reference

### Main Functions

#### `handle_chat(message: str) -> str`

Main entry point for processing user queries.

- **Parameters**: `message` - User query in Arabic or English
- **Returns**: AI-generated response with business insights

#### `process_input(input_text: str) -> str`

Core workflow processing function.

- **Parameters**: `input_text` - Raw user input
- **Returns**: Processed response with data analysis

### Tools Available

- `get_db_schema_and_tables` - Retrieve database schema information
- `get_table_definition` - Get detailed table structure
- `execute_sql_query` - Execute SQL queries safely
- `analyze_schema` - AI-powered schema analysis
- `analyze_columns` - Column-level data analysis
- `save_summary` - Store business insights

## System Behavior

The system follows this workflow:

1. **Language Detection**: Automatically detects Arabic or English input
2. **Entity Extraction**: Identifies business entities (products, customers, dates, amounts)
3. **Schema Discovery**: Finds relevant database tables based on the query
4. **Data Analysis**: Executes SQL queries and analyzes results
5. **Insight Generation**: Provides actionable business recommendations
6. **Response**: Returns insights in the same language as the input

### Key Features

- **Multilingual Support**: Seamlessly handles Arabic and English queries
- **Smart Table Discovery**: Automatically finds relevant tables for analysis
- **Data Quality Checks**: Validates data before providing insights
- **Business Context**: Tailored specifically for Al Balsan Group operations
- **Prototype Awareness**: Transparently communicates data limitations
- **Insight Storage**: Saves valuable findings for future reference

## Development

### Running Tests

```bash
# Test individual components
python test_components.py

# Test complete workflow
python test_workflow.py
```

### Environment Validation

```bash
# Check if all required environment variables are set
python check_env.py
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -am 'Add your feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Create a Pull Request

## Security

- Environment variables are properly managed via `.env` files
- Sensitive information is excluded from version control
- SQL injection protection through parameterized queries
- API keys are never logged or exposed

## License

This project is proprietary software for Al Balsan Group.

## Support

For technical support or questions, contact the development team. 3. Query the database for relevant information 4. Provide business insights and recommendations 5. Respond in the same language as the input 6. Store chat history in the database

## Notes

- The system is currently in prototype phase
- Data may be incomplete or unvalidated
- All responses include a prototype disclaimer when appropriate
- The system uses GPT-4 for natural language processing
- Chat history is persisted in PostgreSQL for context maintenance
