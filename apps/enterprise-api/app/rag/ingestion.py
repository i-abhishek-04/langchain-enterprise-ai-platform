import os
import re
from typing import List, Dict, Any

def markdown_section_splitter(text: str, chunk_size: int = 400, chunk_overlap: int = 80) -> List[str]:
    """
    Markdown-aware document splitter that keeps section headers attached to content blocks.
    Prevents headings from being orphaned or sliced mid-line.
    """
    # Split primarily by Markdown headers
    sections = re.split(r'(?=\n#{1,4} )', text)
    chunks = []

    for sec in sections:
        sec_clean = sec.strip()
        if not sec_clean:
            continue
            
        if len(sec_clean) <= chunk_size:
            chunks.append(sec_clean)
        else:
            # Sub-split long sections cleanly on paragraphs / newlines
            paragraphs = sec_clean.split("\n\n")
            current_chunk = ""
            for p in paragraphs:
                if len(current_chunk) + len(p) + 2 <= chunk_size:
                    current_chunk += ("\n\n" + p if current_chunk else p)
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = p
            if current_chunk:
                chunks.append(current_chunk)

    return chunks if chunks else [text]

def parse_file_content(file_path: str, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    text = ""
    
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text += f"\n--- Page {i+1} ---\n" + extracted
        except Exception:
            pass
    elif ext == ".docx":
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
        except Exception:
            pass

    if not text:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
            
    return text

def process_and_index_document(file_path: str, filename: str, chunk_size: int = 400, chunk_overlap: int = 80) -> Dict[str, Any]:
    raw_text = parse_file_content(file_path, filename)
    if not raw_text.strip():
        raise ValueError("Uploaded document contains no extractable text.")
        
    doc_chunks = markdown_section_splitter(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    from app.rag.vectorstore import upsert_chunks

    formatted_chunks = [
        {
            "text": f"[{filename}] {chunk}",
            "filename": filename,
            "page": 1,
            "chunk_id": idx
        }
        for idx, chunk in enumerate(doc_chunks)
    ]
    
    indexed_count = upsert_chunks(formatted_chunks)
    
    return {
        "filename": filename,
        "raw_text_length": len(raw_text),
        "chunk_count": indexed_count,
        "status": "INDEXED"
    }
