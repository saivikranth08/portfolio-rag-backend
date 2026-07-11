import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables from .env file
load_dotenv()

# 1. Initialize FastAPI
app = FastAPI(title="Sai AI Portfolio Backend")

# 2. Add CORS middleware so your Next.js frontend can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change this to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Setup global variables for the RAG components
vectorstore = None
retriever = None
llm = None
rag_chain = None

# 4. Load the AI models when the server starts
@app.on_event("startup")
async def startup_event():
    global vectorstore, retriever, llm, rag_chain
    print("Loading Embeddings and Vector DB...")
    
    # Load the exact same embedding model used in ingest.py
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Load the Chroma DB from the disk
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    # Create a retriever that fetches the top 3 most relevant chunks of your resume
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    print("Initializing Groq LLM...")
    # Initialize the Groq model (make sure GROQ_API_KEY is in your environment variables)
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.3)
    
    # Create the System Prompt
    system_prompt = """You are a professional, friendly AI assistant for Sai Vikranth Kanuru, an AI Engineer. 
Your goal is to answer questions about Sai's experience, education, and projects to recruiters and visitors.
Always speak in the first person as Sai's assistant. Keep answers concise and strictly based on the context provided.
If the context does not contain the answer, say "I don't have that exact information, but you can email Sai directly at kanuruvikranth@gmail.com."

Context from Sai's Resume:
{context}

User's Question: {question}"""

    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    # Build the RAG chain
    rag_chain = prompt | llm | StrOutputParser()
    print("AI Backend Ready!")

# Define the request body format
class ChatRequest(BaseModel):
    message: str

# 5. Create the Chat Endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Retrieve relevant documents from Chroma
    docs = retriever.invoke(request.message)
    
    # Combine the document text into a single context string
    context_text = "\n\n".join([doc.page_content for doc in docs])
    
    # Run the LLM chain
    response = rag_chain.invoke({
        "context": context_text,
        "question": request.message
    })
    
    return {"reply": response}

@app.get("/")
async def health_check():
    return {"status": "healthy", "message": "Sai's RAG Backend is running"}
