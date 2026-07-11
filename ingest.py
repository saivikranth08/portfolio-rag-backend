import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma

# Configuration
PDF_PATH = "../sai-portfolio/public/Sai_Vikranth_Kanuru_Resume.pdf"
CHROMA_PATH = "./chroma_db"

def main():
    print("Loading Resume PDF...")
    # 1. Load the PDF
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    print("Chunking text...")
    # 2. Split the text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")

    print("Generating embeddings and saving to Chroma...")
    # Initialize the lightweight fastembed model
    embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 4. Save to Chroma Database
    db = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory=CHROMA_PATH
    )
    
    print(f"Success! Embedded {len(chunks)} chunks and saved database to {CHROMA_PATH}")

if __name__ == "__main__":
    main()
