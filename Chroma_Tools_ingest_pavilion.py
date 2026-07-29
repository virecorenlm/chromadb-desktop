#!/usr/bin/env python3
import os, pathlib, uuid
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

BASE_DIR = pathlib.Path.home() / "Chroma_Feed"
COLLECTIONS = {
    "documents": ["txt", "md", "rst"],
    "notes":     ["txt", "md"],
    "logs":      ["log", "txt"],
    "scripts":   ["py", "sh", "bash"],
    "pdfs":      ["pdf"],
    "images":    ["png", "jpg", "jpeg", "webp"],  # (optional OCR later)
    "other":     []
}

def read_text_file(p):
    try:
        return p.read_text(errors="ignore")
    except Exception:
        return ""

def read_pdf_file(p):
    try:
        text = []
        pdf = PdfReader(str(p))
        for page in pdf.pages:
            text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception:
        return ""

def file_to_text(p: pathlib.Path) -> str:
    ext = p.suffix.lower().lstrip(".")
    if ext in {"txt","md","rst","log","py","sh","bash"}:
        return read_text_file(p)
    if ext == "pdf":
        return read_pdf_file(p)
    return ""  # skip images for now

def chunk(text, size=1200, overlap=200):
    text = text.strip()
    out=[]
    i=0
    while i < len(text):
        out.append(text[i:i+size])
        i += size - overlap
    return [c for c in out if c.strip()]

def main():
    client = chromadb.PersistentClient(path=str(pathlib.Path.home() / "Chroma_Data"))
    embed = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    for cname, exts in COLLECTIONS.items():
        col = client.get_or_create_collection(name=cname, embedding_function=embed)
        feed_dir = BASE_DIR / cname
        if not feed_dir.exists():
            continue
        for p in feed_dir.rglob("*"):
            if not p.is_file():
                continue
            if exts and p.suffix.lower().lstrip(".") not in exts:
                continue
            text = file_to_text(p)
            if not text.strip():
                continue
            parts = chunk(text)
            if not parts:
                continue
            ids = [f"{p}:{i}:{uuid.uuid4()}" for i,_ in enumerate(parts)]
            metas = [{"source": str(p), "part": i} for i,_ in enumerate(parts)]
            col.add(documents=parts, metadatas=metas, ids=ids)
            print(f"Indexed: {p} ({len(parts)} chunks)")

if __name__ == "__main__":
    main()