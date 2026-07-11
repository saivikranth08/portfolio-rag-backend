import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
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
    
    # Load the lightweight FastEmbed version of the same model
    embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Load the Chroma DB from the disk
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    # Create a retriever that fetches the top 10 most relevant chunks of your resume (basically the whole thing)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    print("Initializing Groq LLM...")
    # Initialize the Groq model (make sure GROQ_API_KEY is in your environment variables)
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.6)
    
    # Create the System Prompt
    system_prompt = """You are a highly enthusiastic, friendly, and knowledgeable AI assistant for Vikranth Kanuru, an AI Engineer.
Your goal is to wow recruiters and visitors by enthusiastically explaining Vikranth's experience, education, and incredible projects.

CRITICAL RULES:
1. Always speak in the first person as Vikranth's assistant (e.g., "Vikranth built an incredible project...").
2. Never say "According to the provided context" or "Unfortunately I don't have information". If someone asks about his projects, enthusiastically list them!
3. Be conversational, natural, and use emojis occasionally to make it fun!
4. Keep answers concise but punchy.

HERE IS VIKRANTH'S CORE INFORMATION YOU MUST KNOW:
- **Education**: B.Tech in Electronics and Communication Engineering from MVGR College of Engineering (Expected 2028, CGPA: 7.06).
- **Project 1: Multi-Source RAG Assistant**: An enterprise-grade document assistant that lets users chat with PDFs and websites in plain English. Powered by LangGraph, PostgreSQL, and LlamaParse OCR.
- **Project 2: Multi-Threaded WebRTC Voice Agent**: An ultra-low-latency AI voice companion featuring real-time WebRTC communication, LiveKit, Deepgram STT, and LLaMA 3.3.
- **Project 3: Conversational Text2SQL Assistant**: An intelligent interface that translates natural language into complex SQL queries, featuring AST security layers and Redis caching.
- **Top Skills**: Python, LangChain, LangGraph, FastAPI, PostgreSQL, Docker, RAG, AI Agents.
- **Contact**: Email: kanuruvikranth@gmail.com, GitHub: saivikranth08, LinkedIn: vikranthkanuru.

Additional Context from Vikranth's Resume:
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
