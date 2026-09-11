import pytest
from app.retrieval.chunker import TextChunker

def test_chunker_basic():
    chunker = TextChunker(chunk_size=10, overlap=5)
    text = "one two three four five six seven eight nine ten eleven twelve thirteen"
    metadata = {"page_id": "test_page"}
    
    chunks = chunker.chunk_text(text, metadata)
    
    assert len(chunks) == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["page_id"] == "test_page"
    assert chunks[0]["chunk_id"] == "test_page-0"
    assert "one two three four five six seven eight nine ten" == chunks[0]["text"]
    
    # Second chunk should overlap by 5
    assert chunks[1]["chunk_index"] == 1
    assert "six seven eight nine ten eleven twelve thirteen" == chunks[1]["text"]

def test_chunker_short_text():
    chunker = TextChunker(chunk_size=10, overlap=5)
    text = "short text"
    metadata = {"page_id": "test_page"}
    
    chunks = chunker.chunk_text(text, metadata)
    
    assert len(chunks) == 1
    assert chunks[0]["text"] == "short text"
    assert chunks[0]["chunk_index"] == 0
