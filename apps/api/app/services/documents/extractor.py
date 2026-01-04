"""Text extraction and chunking for documents."""

import csv
import io
from typing import Iterator

# PDF extraction - try pdfplumber first
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def extract_text_from_pdf(file_content: bytes) -> list[tuple[int, str]]:
    """Extract text from PDF file.
    
    Returns list of (page_number, text) tuples.
    """
    if not HAS_PDFPLUMBER:
        raise RuntimeError("pdfplumber not installed. Install with: pip install pdfplumber")
    
    pages: list[tuple[int, str]] = []
    
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((i, text))
    
    return pages


def extract_text_from_txt(file_content: bytes) -> list[tuple[int, str]]:
    """Extract text from TXT/MD file.
    
    Returns list of (page_number, text) tuples.
    Page number is always 1 for plain text files.
    """
    text = file_content.decode("utf-8", errors="ignore")
    return [(1, text)] if text.strip() else []


def extract_text_from_csv(file_content: bytes) -> list[tuple[int, str]]:
    """Extract text from CSV file.
    
    Returns list of (row_number, text) tuples.
    """
    text = file_content.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    
    rows: list[tuple[int, str]] = []
    for i, row in enumerate(reader, 1):
        row_text = " | ".join(row)
        if row_text.strip():
            rows.append((i, row_text))
    
    return rows


def extract_text(filename: str, file_content: bytes) -> list[tuple[int, str]]:
    """Extract text from file based on extension.
    
    Returns list of (page/row_number, text) tuples.
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    
    if ext == "pdf":
        return extract_text_from_pdf(file_content)
    elif ext in ("txt", "md", "markdown"):
        return extract_text_from_txt(file_content)
    elif ext == "csv":
        return extract_text_from_csv(file_content)
    else:
        # Try as plain text
        try:
            return extract_text_from_txt(file_content)
        except Exception:
            raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> Iterator[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Target size of each chunk
        overlap: Number of characters to overlap between chunks
    
    Yields:
        Text chunks
    """
    if not text:
        return
    
    # Clean text
    text = " ".join(text.split())
    
    if len(text) <= chunk_size:
        yield text
        return
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence ending
            for i in range(min(100, end - start), 0, -1):
                if end - i < len(text) and text[end - i] in ".!?":
                    end = end - i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        
        # Move start with overlap
        start = end - overlap
        if start < 0:
            start = end


def process_document_text(
    pages: list[tuple[int, str]],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """Process extracted text into chunks.
    
    Returns list of dicts with:
        - chunk_index: int
        - text: str
        - page_number: int | None
    """
    chunks: list[dict] = []
    chunk_idx = 0
    
    for page_num, page_text in pages:
        for chunk_str in chunk_text(page_text, chunk_size, overlap):
            chunks.append({
                "chunk_index": chunk_idx,
                "text": chunk_str,
                "page_number": page_num,
            })
            chunk_idx += 1
    
    return chunks
