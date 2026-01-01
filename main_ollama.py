import asyncio
import json
import time
import requests
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "ministral-3:8b"

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

def call_ollama(messages, tools):
    """Call Ollama API with tool support"""
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": tools,
        "stream": False
    }
    
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] Ollama request | Messages: {len(messages)} | Tools: {len(tools)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        elapsed = time.time() - start_time
        result = response.json()
        
        # Log response summary
        tool_calls = result.get('message', {}).get('tool_calls', [])
        if tool_calls:
            tool_names = [tc['function']['name'] for tc in tool_calls]
            print(f"[{time.strftime('%H:%M:%S')}] Response in {elapsed:.2f}s | Tool calls: {', '.join(tool_names)}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Response in {elapsed:.2f}s | Final answer")
        
        return result
        
    except requests.exceptions.Timeout:
        print(f"[ERROR] Request timeout after {time.time() - start_time:.2f}s")
        raise
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection error: {e}")
        print("[ERROR] Make sure Ollama is running on port 11434")
        raise
    except Exception as e:
        print(f"[ERROR] {e}")
        raise

async def run_mcp_async(user_query: str) -> dict:
    """Execute query via MCP server"""
    
    # Configure MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get tools from MCP server
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
            
            print(f"[MCP] Connected to server | {len(tools)} tools available")
            print(f"[USER] {user_query}\n")
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ]
            
            # Interaction loop
            for iteration in range(10):
                print(f"--- Iteration {iteration + 1} ---")
                
                # Call Ollama
                response = call_ollama(messages, tools)
                
                message = response.get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                
                # If no tool calls, we're done
                if not tool_calls:
                    print(f"\n[FINAL ANSWER]\n{content}\n")
                    return {"result": content or "No response"}
                
                # Add assistant message
                messages.append(message)
                
                # Execute tool calls via MCP
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]
                    
                    # Parse arguments if string
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)
                    
                    print(f"[MCP] Executing: {tool_name}({json.dumps(tool_args)})")
                    
                    # Call tool via MCP server
                    result = await session.call_tool(tool_name, tool_args)
                    result_text = "".join(c.text for c in result.content if hasattr(c, "text"))
                    
                    # Show result preview
                    result_preview = result_text[:100] + "..." if len(result_text) > 100 else result_text
                    print(f"[MCP] Result: {result_preview}\n")
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "content": result_text
                    })
            
            return {"result": "Max iterations reached", "messages": messages}

def run_mcp(user_query: str) -> dict:
    """Synchronous interface for run_mcp"""
    return asyncio.run(run_mcp_async(user_query))

if __name__ == "__main__":
    # Check Ollama connection
    print("="*70)
    print("Checking Ollama connection...")
    print("="*70)
    
    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if test_response.status_code == 200:
            models = test_response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f"[OK] Ollama is running")
            print(f"[OK] Available models: {', '.join(model_names)}")
            
            if MODEL in model_names:
                print(f"[OK] Model '{MODEL}' is ready")
            else:
                print(f"[ERROR] Model '{MODEL}' not found")
                print(f"[INFO] Run: ollama pull {MODEL}")
                exit(1)
        else:
            print(f"[ERROR] Ollama responded with status {test_response.status_code}")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Ollama at http://localhost:11434")
        print("[INFO] Make sure Ollama is running")
        exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)
    
    print("="*70)
    print()
    
    # Execute query
    result = run_mcp(
        "List the names and ages of devs from the backend team sorted by descending age"
    )
    
    print("="*70)
    print("RESULT")
    print("="*70)
    print(result)
