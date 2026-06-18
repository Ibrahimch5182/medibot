from app.rag.hybrid_rag import hybrid_rag_chain


question = "What is the staff leave policy?"
role = "nurse"

result = hybrid_rag_chain(question=question, role=role)

print(result)