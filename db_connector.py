"""
db_connector.py
Handles MySQL connection, schema introspection, safety checks, and query execution.
"""

import time
import re
import pymysql
import pandas as pd
from typing import Dict, Any, Tuple, List

# Disallowed keywords to enforce read-only execution
DANGEROUS_SQL_KEYWORDS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b",
    r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bREPLACE\b",
    r"\bGRANT\b", r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b",
    r"\bSHUTDOWN\b", r"\bCALL\b"
]

class MySQLConnector:
    def __init__(self, host="localhost", port=3306, user="root", password="", database="retail_analytics_db"):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.database = database

    def get_connection(self):
        """Creates and returns a pymysql connection."""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database if self.database else None,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5,
            autocommit=True
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Tests if the database connection succeeds."""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS test;")
                result = cursor.fetchone()
            conn.close()
            return True, "Successfully connected to MySQL database!"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_all_databases(self) -> List[str]:
        """Returns list of accessible databases."""
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5
            )
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES;")
                rows = cursor.fetchall()
            conn.close()
            return [row["Database"] for row in rows if row["Database"] not in ("information_schema", "mysql", "performance_schema", "sys")]
        except Exception:
            return []

    def get_schema_info(self) -> Dict[str, Any]:
        """Fetches detailed table schemas, column types, and foreign keys."""
        schema = {}
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                # 1. Fetch all tables
                cursor.execute("SHOW TABLES;")
                table_key = f"Tables_in_{self.database}"
                tables = [row[table_key] if table_key in row else list(row.values())[0] for row in cursor.fetchall()]

                for table in tables:
                    # 2. Columns
                    cursor.execute(f"DESCRIBE `{table}`;")
                    cols = cursor.fetchall()
                    schema[table] = {
                        "columns": [
                            {
                                "name": c["Field"],
                                "type": c["Type"],
                                "key": c["Key"],
                                "nullable": c["Null"] == "YES"
                            }
                            for c in cols
                        ]
                    }

                # 3. Foreign key relationships
                fk_query = """
                SELECT 
                    TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM 
                    INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE 
                    TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL;
                """
                cursor.execute(fk_query, (self.database,))
                fks = cursor.fetchall()
                for fk in fks:
                    tbl = fk["TABLE_NAME"]
                    if tbl in schema:
                        if "foreign_keys" not in schema[tbl]:
                            schema[tbl]["foreign_keys"] = []
                        schema[tbl]["foreign_keys"].append({
                            "column": fk["COLUMN_NAME"],
                            "ref_table": fk["REFERENCED_TABLE_NAME"],
                            "ref_column": fk["REFERENCED_COLUMN_NAME"]
                        })

            conn.close()
            return schema
        except Exception as e:
            return {"error": str(e)}

    def get_schema_prompt_text(self) -> str:
        """Formats the schema into a concise, token-efficient prompt for the LLM."""
        schema = self.get_schema_info()
        if "error" in schema:
            return f"Error retrieving schema: {schema['error']}"

        prompt_lines = [f"MySQL Database: `{self.database}`\nTables and Columns:"]
        for table, details in schema.items():
            col_strs = []
            for col in details.get("columns", []):
                flags = []
                if col["key"] == "PRI":
                    flags.append("PK")
                elif col["key"] == "MUL":
                    flags.append("FK/Index")
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                col_strs.append(f"  - `{col['name']}` ({col['type']}){flag_str}")
            
            prompt_lines.append(f"\nTable `{table}`:")
            prompt_lines.extend(col_strs)
            
            fks = details.get("foreign_keys", [])
            if fks:
                prompt_lines.append("  Foreign Keys:")
                for fk in fks:
                    prompt_lines.append(f"    - `{fk['column']}` references `{fk['ref_table']}`(`{fk['ref_column']}`)")
                    
        return "\n".join(prompt_lines)

    def validate_query_safety(self, sql: str) -> Tuple[bool, str]:
        """Ensures query is read-only (SELECT / WITH)."""
        clean_sql = re.sub(r"--.*?\n", "", sql) # remove single line comments
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL) # remove multi-line comments
        clean_sql_upper = clean_sql.strip().upper()

        if not (clean_sql_upper.startswith("SELECT") or clean_sql_upper.startswith("WITH") or clean_sql_upper.startswith("SHOW") or clean_sql_upper.startswith("EXPLAIN")):
            return False, "Security Error: Only SELECT queries are permitted."

        for pattern in DANGEROUS_SQL_KEYWORDS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                return False, f"Security Violation: Query contains prohibited keyword matching {pattern}."

        return True, "Query verified safe."

    def execute_query(self, sql: str) -> Tuple[bool, Any, float]:
        """
        Executes a validated read-only SQL query and returns (success, dataframe_or_error, execution_time_seconds).
        """
        is_safe, msg = self.validate_query_safety(sql)
        if not is_safe:
            return False, msg, 0.0

        start_time = time.time()
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
            conn.close()

            df = pd.DataFrame(rows)
            duration = round(time.time() - start_time, 3)
            return True, df, duration
        except Exception as e:
            duration = round(time.time() - start_time, 3)
            return False, str(e), duration
