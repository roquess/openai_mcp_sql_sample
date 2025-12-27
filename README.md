# MCP SQL Tutorial

## Overview

The MCP workflow is inspired by the **Model Context Protocol (MCP) from Anthropic** (introduced in 2024) and follows a structured, tool-based approach:

1. **Describe tables**: Retrieve the structure of the database tables.
2. **Get column values**: Use `column_values` to discover distinct values for filtering.
3. **Construct SQL query**: The model builds a query using only the available tools.
4. **Execute query**: Run the query with `execute_query` and return results.

The model never executes SQL itself. All interactions pass through defined tools, ensuring predictable and safe operations.

## Example

User input:

```
List the names and ages of devs from the backend team sorted by descending age
```

MCP behavior:

1. Calls `column_values` to get distinct roles and teams.
2. Constructs the query:

```sql
SELECT name, age FROM employees
WHERE role = 'dev' AND team = 'backend'
ORDER BY age DESC
```

3. Executes the query and returns:

```json
{
  "result": [
    {"name": "Charlie", "age": 35},
    {"name": "Bob", "age": 28}
  ]
}
```

## Key Points

* MCP is **tool-based**, ensuring the LLM cannot run SQL directly.
* The model uses only the **table description** and user input to generate queries.
* Results are returned in a structured and predictable format.
* This tutorial follows the **MCP philosophy**, allowing flexible, auditable, and secure LLM interactions with external data.

## Start

```
python setup_db.py
python main.py
```

## License

This project is released under the **MIT License**, allowing free use, modification, and distribution.

## Sources

1. Anthropic Blog – Model Context Protocol Overview: [https://www.anthropic.com/news/model-context-protocol](https://www.anthropic.com/news/model-context-protocol)
2. Wikipedia – Model Context Protocol: [https://en.wikipedia.org/wiki/Model_Context_Protocol](https://en.wikipedia.org/wiki/Model_Context_Protocol)

