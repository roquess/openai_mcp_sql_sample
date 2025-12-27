import sqlite3

DB_PATH = "company.db"

def describe_tables() -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()

    desc = {}
    for (table_name,) in tables:
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        desc[table_name] = [{"name": col[1], "type": col[2]} for col in columns]

    conn.close()
    return {"result": desc}


def column_values(table_name: str, column_name: str) -> dict:
    print(f"[MCP] column_values called with table='{table_name}', column='{column_name}'")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT DISTINCT {column_name} FROM {table_name}")
    values = [v[0] for v in c.fetchall() if v[0] is not None]
    conn.close()
    return {"result": values}


def execute_query(query: str) -> dict:
    print("[MCP] execute_query QUERY =", query)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(query)
        rows = c.fetchall()
        columns = [desc[0] for desc in c.description] if c.description else []
        result = [dict(zip(columns, row)) for row in rows]
        conn.commit()
    except Exception as e:
        result = {"error": str(e)}
    conn.close()
    print("[MCP] execute_query RESULT =", result)
    return {"result": result}

