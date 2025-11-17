import pdfplumber
import os
import glob
import re

from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from chromadb import PersistentClient
from app.config import OPENAI_API_KEY, EMBEDDING_MODEL

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "annual_reports"


def extract_metadata(file_path: str):
    """Extract company and year from filename."""
    filename = os.path.basename(file_path)

    # Company from parent folder
    company = os.path.basename(os.path.dirname(file_path))

    # Extract year from filename using regex
    year_match = re.search(r"(20\d{2})", filename)
    year = int(year_match.group(1)) if year_match else None

    return company, year


def ingest_all_pdfs():
    print("Scanning for PDF reports...")

    pdf_paths = glob.glob("data/*/*.pdf")

    print(f"Found {len(pdf_paths)} PDF files.")

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY,
    )

    client = PersistentClient(path=CHROMA_PATH)
    coll = client.get_or_create_collection(name=COLLECTION_NAME)

    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50)

    for pdf_path in pdf_paths:
        print(f"\nIngesting {pdf_path}")

        company, year = extract_metadata(pdf_path)
        print(f"   → Company: {company}, Year: {year}")

        # Load and extract text
        with pdfplumber.open(pdf_path) as pdf:
            pages = [p.extract_text() for p in pdf.pages]

        pages = [p for p in pages if p]

        text = "\n\n".join(pages)

        chunks = splitter.split_text(text)
        print(f"Created {len(chunks)} chunks")

        BATCH = 128
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i+BATCH]
            vectors = embeddings.embed_documents(batch)

            coll.add(
                documents=batch,
                embeddings=vectors,
                metadatas=[
                    {
                        "company": company,
                        "year": year,
                        "source": pdf_path,
                    }
                    for _ in batch
                ],
                ids=[str(hash(company + str(year) + chunk)) for chunk in batch],
            )

        print(f"Completed ingestion for {pdf_path}")

    print("All PDFs ingested successfully!")
    

if __name__ == "__main__":
    ingest_all_pdfs()
