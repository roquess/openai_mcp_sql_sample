from mcp_server import run_mcp

if __name__ == "__main__":
    result = run_mcp(
        "List the names and ages of devs from the backend team sorted by descending age"
    )
    print("\n[FINAL RESULT]")
    print(result)

