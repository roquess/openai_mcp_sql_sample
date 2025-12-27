import json
from openai import OpenAI
from tools import describe_tables, column_values, execute_query

client = OpenAI()

SYSTEM_PROMPT = """
You are not allowed to execute SQL queries yourself.
All access to the database must go through a tool.
Use the tools to get distinct values and construct the final query.
"""

TOOLS_DEF = [
    {
        "type": "function",
        "function": {
            "name": "execute_query",
            "description": "Executes a SQL query and returns the result",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "column_values",
            "description": "Returns distinct values of a column",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"},
                    "column_name": {"type": "string"}
                },
                "required": ["table_name", "column_name"]
            }
        }
    }
]

def run_mcp(user_input: str) -> dict:
    print(f"[USER] {user_input}")

    table_desc = describe_tables()
    print(f"[MCP INTERNAL] Table description: {table_desc}")

    enhanced_system_prompt = SYSTEM_PROMPT + "\n" + json.dumps(table_desc, indent=2)

    messages = [
        {"role": "system", "content": enhanced_system_prompt},
        {"role": "user", "content": user_input}
    ]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS_DEF,
            tool_choice="required"
        )

        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", [])

        if not tool_calls:
            print("[MCP] Final response:", message.content)
            return {"result": message.content}

        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": message.tool_calls
        })

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            if tool_name == "column_values":
                result = column_values(**args)
            elif tool_name == "execute_query":
                result = execute_query(**args)
                return result
            else:
                raise RuntimeError(f"Unexpect Tool called : {tool_name}")

            print(f"[MCP] {tool_name} RESULT =", result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

