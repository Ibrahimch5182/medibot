"""
SQL RAG chain for MediBot.

Assignment requirement:
Implement a plain Python function:

    sql_rag_chain(question: str) -> str

with 3 explicit steps:

1. Translate natural language question into SQL using an LLM
2. Clean raw LLM output to extract only SQL
3. Execute SQL, then pass result back to LLM for final answer

Important:
SQL RAG is only allowed for billing_executive and admin.
That role check will also be enforced later in FastAPI routing.
"""

import re
import sqlite3
from pathlib import Path
from typing import Any, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.rag.llm import get_llm


DB_PATH = Path(settings.DATA_DIR) / "db" / "mediassist.db"


SCHEMA_DESCRIPTION = """
SQLite database schema:

Table: claims
Columns:
- claim_id TEXT PRIMARY KEY
- patient_id TEXT
- patient_name TEXT
- department TEXT
- claim_type TEXT
- diagnosis_code TEXT
- insurer TEXT
- claimed_amount REAL
- approved_amount REAL
- status TEXT
- submitted_date TEXT in YYYY-MM-DD format
- resolved_date TEXT in YYYY-MM-DD format, nullable

Table: maintenance_tickets
Columns:
- ticket_id TEXT PRIMARY KEY
- equipment_name TEXT
- equipment_id TEXT
- category TEXT
- campus TEXT
- issue_type TEXT
- fault_code TEXT
- raised_by TEXT
- raised_date TEXT in YYYY-MM-DD format
- resolved_date TEXT in YYYY-MM-DD format, nullable
- status TEXT
- resolution_note TEXT
"""


def clean_sql(raw_output: str) -> str:
    """
    Extract only the SQL statement from LLM output.

    LLMs often return:
    ```sql
    SELECT ...
    ```
    or explanations before/after SQL.

    This function keeps only the executable SQL.
    """

    text = raw_output.strip()

    # Remove markdown code fences
    text = re.sub(r"```sql", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    # Find first SELECT/WITH statement
    match = re.search(
        r"(SELECT|WITH)\s+.*",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        raise ValueError(f"No valid SQL found in LLM output: {raw_output}")

    sql = match.group(0).strip()

    # Keep only first statement
    if ";" in sql:
        sql = sql.split(";")[0] + ";"

    return sql


def execute_sql(sql: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Execute SQL safely against SQLite database.

    We only allow read-only SELECT/WITH queries.
    """

    normalized = sql.strip().lower()

    if not (
        normalized.startswith("select")
        or normalized.startswith("with")
    ):
        raise ValueError("Only read-only SELECT/WITH SQL queries are allowed.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(sql)

    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    conn.close()

    return columns, rows


def generate_sql(question: str) -> str:
    """
    Ask the LLM to convert a question into SQLite SQL.
    """

    llm = get_llm(temperature=0)

    system_prompt = f"""
You are a careful SQLite analyst.

Convert the user's question into a single read-only SQLite query.

Rules:
- Use only the schema provided below.
- Do not invent tables or columns.
- Return only SQL.
- Do not include explanations.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
- Dates are stored as text in YYYY-MM-DD format.
- Use SQLite functions such as strftime when needed.
- Text values in the database are lowercase. Always compare text fields using LOWER(column) = 'lowercase_value'.

{SCHEMA_DESCRIPTION}
"""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
    )

    return clean_sql(response.content)


def generate_final_answer(
    question: str,
    sql: str,
    columns: List[str],
    rows: List[Tuple[Any, ...]],
) -> str:
    """
    Ask the LLM to explain the SQL result in natural language.
    """

    llm = get_llm(temperature=0.1)

    result_preview = {
        "columns": columns,
        "rows": rows[:50],
        "row_count_returned": len(rows),
    }

    system_prompt = """
You are MediBot's analytical assistant.

Answer the user's question using only the SQL query result.
Be concise and mention key numbers clearly.
If the result is empty, say no matching records were found.
"""

    user_prompt = f"""
Question:
{question}

SQL used:
{sql}

SQL result:
{result_preview}

Provide the final answer.
"""

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    return response.content


def sql_rag_chain(question: str) -> str:
    """
    Plain Python SQL RAG function required by the assignment.
    """

    sql = generate_sql(question)

    columns, rows = execute_sql(sql)

    answer = generate_final_answer(
        question=question,
        sql=sql,
        columns=columns,
        rows=rows,
    )

    return answer