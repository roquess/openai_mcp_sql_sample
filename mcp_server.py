import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
from tools import describe_tables, column_values, execute_query

app = Server("sql-tools-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="describe_tables",
            description="Returns the schema of all available tables",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="column_values",
            description="Returns distinct values of a column in a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "column_name": {
                        "type": "string",
                        "description": "Name of the column"
                    }
                },
                "required": ["table_name", "column_name"]
            }
        ),
        Tool(
            name="execute_query",
            description="Executes a SQL query and returns the result",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The SQL query to execute"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "describe_tables":
            result = describe_tables()
        elif name == "column_values":
            result = column_values(
                table_name=arguments["table_name"],
                column_name=arguments["column_name"]
            )
        elif name == "execute_query":
            result = execute_query(query=arguments["query"])
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
