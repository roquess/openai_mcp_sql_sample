import asyncio
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

client = OpenAI()

SYSTEM_PROMPT = """
You are a SQL assistant with access to database tools.

MANDATORY WORKFLOW - Follow these steps IN ORDER:
1. ALWAYS call describe_tables first to understand the schema
2. For ANY query with WHERE conditions (filtering by role, team, status, etc.):
   - MUST call column_values for EACH column used in WHERE clause
   - This ensures you use the EXACT values that exist in the database
   - Example: If filtering by 'role' and 'team', call column_values twice
3. Only after getting exact values, construct and execute_query

CRITICAL: Never guess column values. Always use column_values to get distinct values before filtering.

Example workflow for "List backend developers":
- Step 1: describe_tables() 
- Step 2: column_values(table_name="employees", column_name="team")
- Step 3: column_values(table_name="employees", column_name="role")  
- Step 4: execute_query with the EXACT values found

Always explain your reasoning before calling tools.
"""

async def run_mcp_async(user_query: str) -> dict:
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools_response = await session.list_tools()
            tools = []
            for tool in tools_response.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
            
            print(f"[USER] {user_query}")
            print(f"[MCP] Connected to server, {len(tools)} tools available\n")
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ]
            
            for iteration in range(10):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                
                if message.content:
                    print(f"[OPENAI] {message.content}\n")
                
                if not message.tool_calls:
                    return {"result": message.content or "No response"}
                
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"[MCP] Calling: {tool_name}({json.dumps(tool_args)})")
                    
                    result = await session.call_tool(tool_name, tool_args)
                    result_text = "".join(c.text for c in result.content if hasattr(c, "text"))
                    
                    print(f"[MCP] Result: {result_text[:150]}...\n")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })
            
            return {"result": "Max iterations reached"}

def run_mcp(user_query: str) -> dict:
    return asyncio.run(run_mcp_async(user_query))

if __name__ == "__main__":
    result = run_mcp(
        "List the names and ages of devs from the backend team sorted by descending age"
    )
    print("\n[FINAL RESULT]")
    print(result)
