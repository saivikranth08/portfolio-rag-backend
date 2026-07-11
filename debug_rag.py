import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

print("Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

print("Testing retriever...")
docs = retriever.invoke("What is his name ?")
print("Found docs:", len(docs))
for d in docs:
    print(d.page_content[:50])

print("Testing LLM...")
llm = ChatGroq(model_name="llama3-8b-8192", temperature=0.3)
system_prompt = """You are a professional, friendly AI assistant...
Context: {context}
Question: {question}"""
prompt = ChatPromptTemplate.from_template(system_prompt)
rag_chain = prompt | llm | StrOutputParser()

context_text = "\n\n".join([doc.page_content for doc in docs])
try:
    response = rag_chain.invoke({"context": context_text, "question": "What is his name ?"})
    print("Success:", response)
except Exception as e:
    import traceback
    traceback.print_exc()
