import os
import re
from typing import List, Dict, Any, Tuple


def split_paragraph_with_overlap(text: str, chunk_size: int = 400, chunk_overlap: int = 80) -> List[str]:
    """
    Split a long paragraph into chunks of at most chunk_size characters with chunk_overlap,
    cutting strictly on whitespace boundaries without splitting words.
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    n = len(words)
    while i < n:
        chunk_words = []
        curr_len = 0
        j = i
        while j < n:
            word = words[j]
            add_len = len(word) if not chunk_words else len(word) + 1
            if curr_len + add_len <= chunk_size or not chunk_words:
                chunk_words.append(word)
                curr_len += add_len
                j += 1
            else:
                break
        chunks.append(" ".join(chunk_words))
        if j >= n:
            break
        overlap_len = 0
        next_i = j
        while next_i > i:
            w_len = len(words[next_i - 1]) + 1
            if overlap_len + w_len <= chunk_overlap:
                overlap_len += w_len
                next_i -= 1
            else:
                break
        if next_i == j:
            i = max(i + 1, j)
        else:
            i = max(i + 1, next_i)
    return chunks


def split_text_with_overlap(text: str, chunk_size: int = 400, chunk_overlap: int = 80) -> List[str]:
    """Split text into chunks cutting strictly on whitespace without splitting words."""
    return split_paragraph_with_overlap(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def markdown_section_splitter(text: str, chunk_size: int = 400, chunk_overlap: int = 80) -> List[str]:
    """
    Markdown-aware document splitter that keeps section headers attached to content blocks.
    Splits long sections on paragraphs first without overlap.
    Applies overlap only when a single paragraph exceeds chunk_size, cutting on whitespace.
    """
    sections = re.split(r'(?=\n#{1,4} )', text)
    all_chunks = []

    for sec in sections:
        sec_clean = sec.strip()
        if not sec_clean:
            continue
        if len(sec_clean) <= chunk_size:
            all_chunks.append(sec_clean)
            continue

        # Split long sections on paragraphs first
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', sec_clean) if p.strip()]
        if not paragraphs:
            continue

        current_group: List[str] = []
        current_len = 0

        for p in paragraphs:
            if len(p) <= chunk_size:
                add_len = len(p) if not current_group else len(p) + 2
                if current_len + add_len <= chunk_size:
                    current_group.append(p)
                    current_len += add_len
                else:
                    if current_group:
                        all_chunks.append("\n\n".join(current_group))
                    current_group = [p]
                    current_len = len(p)
            else:
                # Single paragraph exceeds chunk_size: apply overlap and cut on whitespace
                if current_group:
                    all_chunks.append("\n\n".join(current_group))
                    current_group = []
                    current_len = 0
                sub_chunks = split_paragraph_with_overlap(p, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                all_chunks.extend(sub_chunks)

        if current_group:
            all_chunks.append("\n\n".join(current_group))

    return all_chunks if all_chunks else [text]


def parse_pdf_pages(file_path: str, filename: str) -> List[Tuple[int, str]]:
    """Extract text page-by-page from a PDF file. Raises ValueError on broken files."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages):
            extracted = page.extract_text()
            if extracted and extracted.strip():
                pages.append((i + 1, extracted.strip()))
        if not pages:
            raise ValueError(f"PDF document '{filename}' contains no extractable text.")
        return pages
    except Exception as exc:
        raise ValueError(f"Failed to parse PDF document '{filename}': {str(exc)}") from exc


def parse_docx(file_path: str, filename: str) -> str:
    """Extract text from a DOCX file. Raises ValueError on broken files."""
    try:
        from docx import Document as DocxDocument
        doc = DocxDocument(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
        if not paragraphs:
            raise ValueError(f"DOCX document '{filename}' contains no extractable text.")
        return "\n\n".join(paragraphs)
    except Exception as exc:
        raise ValueError(f"Failed to parse DOCX document '{filename}': {str(exc)}") from exc


def parse_plain_text(file_path: str, filename: str) -> str:
    """Read plain text or markdown document."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    if not text.strip():
        raise ValueError(f"Document '{filename}' contains no extractable text.")
    return text


def parse_file_content(file_path: str, filename: str) -> str:
    """Parse text content from supported file types."""
    base_name = os.path.basename(filename)
    ext = os.path.splitext(base_name)[1].lower()
    if ext == ".pdf":
        pages = parse_pdf_pages(file_path, base_name)
        return "\n\n".join(f"--- Page {p} ---\n{t}" for p, t in pages)
    elif ext == ".docx":
        return parse_docx(file_path, base_name)
    else:
        return parse_plain_text(file_path, base_name)


def process_and_index_document(
    file_path: str,
    filename: str,
    chunk_size: int = 400,
    chunk_overlap: int = 80
) -> Dict[str, Any]:
    base_name = os.path.basename(filename)
    ext = os.path.splitext(base_name)[1].lower()

    formatted_chunks = []
    total_raw_length = 0

    if ext == ".pdf":
        pages = parse_pdf_pages(file_path, base_name)
        chunk_idx = 0
        for page_num, page_text in pages:
            total_raw_length += len(page_text)
            chunks = markdown_section_splitter(page_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            for chunk in chunks:
                formatted_chunks.append({
                    "text": f"[{base_name}] {chunk}",
                    "filename": base_name,
                    "page": page_num,
                    "chunk_id": chunk_idx,
                })
                chunk_idx += 1
    elif ext == ".docx":
        raw_text = parse_docx(file_path, base_name)
        total_raw_length = len(raw_text)
        chunks = markdown_section_splitter(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for idx, chunk in enumerate(chunks):
            formatted_chunks.append({
                "text": f"[{base_name}] {chunk}",
                "filename": base_name,
                "page": 1,
                "chunk_id": idx,
            })
    else:
        raw_text = parse_plain_text(file_path, base_name)
        total_raw_length = len(raw_text)
        chunks = markdown_section_splitter(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for idx, chunk in enumerate(chunks):
            formatted_chunks.append({
                "text": f"[{base_name}] {chunk}",
                "filename": base_name,
                "page": 1,
                "chunk_id": idx,
            })

    if not formatted_chunks:
        raise ValueError(f"Uploaded document '{base_name}' contains no extractable text.")

    from app.rag.vectorstore import upsert_chunks
    indexed_count = upsert_chunks(formatted_chunks)

    return {
        "filename": base_name,
        "raw_text_length": total_raw_length,
        "chunk_count": indexed_count,
        "status": "INDEXED",
    }
