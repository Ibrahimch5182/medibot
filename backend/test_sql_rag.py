from app.rag.sql_rag import generate_sql, execute_sql, sql_rag_chain


questions = [
    "How many claims are pending?",
    "What is the total claimed amount by department?",
    "Which equipment category has the most open maintenance tickets?",
    "How many maintenance tickets are escalated?",
]


for question in questions:
    print("\n" + "=" * 100)
    print("QUESTION:", question)
    print("=" * 100)

    sql = generate_sql(question)
    print("\nSQL:")
    print(sql)

    columns, rows = execute_sql(sql)
    print("\nCOLUMNS:")
    print(columns)

    print("\nROWS:")
    for row in rows[:10]:
        print(row)

    answer = sql_rag_chain(question)
    print("\nANSWER:")
    print(answer)