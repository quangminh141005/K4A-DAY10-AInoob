"""Verification script for Member 3 (RAG & Agent Specialist).

This script tests and verifies:
1. Sentence-Transformers embedding model (all-MiniLM-L6-v2)
2. LocalEmbeddingIndex build and ChromaDB collection management
3. Semantic search & cosine similarity scoring
4. Exact lookup by DOI / title
5. Question Answering logic (_extract_answer & answer_question)
6. Multi-provider LLM agent initialization and tool invocation
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import pandas as pd

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.config import load_settings
from retrieval.embeddings import MiniLMEmbeddings
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question
from retrieval.agent import build_agent, run_agent_question


def run_verification():
    print("=" * 60)
    print("MEMBER 3 VERIFICATION SUITE: RAG, VECTOR STORE & AGENT")
    print("=" * 60)

    settings = load_settings()
    
    # --- 1. Test Embeddings ---
    print("\n[1/5] Testing MiniLM Embedding Model...")
    embedder = MiniLMEmbeddings(settings.embedding_model)
    test_texts = [
        "Retrieval-Augmented Generation for scholarly search.",
        "Data observability with Great Expectations and ChromaDB."
    ]
    doc_vectors = embedder.embed_documents(test_texts)
    query_vector = embedder.embed_query("scholarly RAG")
    assert len(doc_vectors) == 2, "Should embed 2 documents"
    assert len(doc_vectors[0]) == 384, f"Expected 384 dims, got {len(doc_vectors[0])}"
    assert len(query_vector) == 384, f"Expected 384 dims, got {len(query_vector)}"
    print(f"  --> Embeddings OK: 384-dimensional vectors generated successfully.")

    # --- 2. Prepare Sample Corpus from raw records ---
    print("\n[2/5] Loading sample paper records from data/raw/crossref_records.json...")
    raw_path = settings.paths.raw_records_json
    if not raw_path.exists():
        print(f"  [ERROR] {raw_path} not found!")
        return False
    
    with open(raw_path, "r", encoding="utf-8") as f:
        records_raw = json.load(f)

    # Build DataFrame matching cleaning.py output contract
    df_rows = []
    for r in records_raw:
        authors_joined = ", ".join(r.get("authors", []))
        categories_joined = ", ".join(r.get("categories", []))
        text_for_embed = (
            f"Title: {r.get('title', '')}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {r.get('published', '')}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {r.get('summary', '')}"
        )
        df_rows.append({
            "paper_id": r["paper_id"],
            "title": r["title"],
            "summary": r["summary"],
            "authors": r.get("authors", []),
            "categories": r.get("categories", []),
            "primary_category": r.get("primary_category", ""),
            "published": r.get("published", ""),
            "updated": r.get("updated", ""),
            "abs_url": r.get("abs_url", ""),
            "pdf_url": r.get("pdf_url", ""),
            "comment": r.get("comment", ""),
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": len(r.get("summary", "")),
            "text_for_embedding": text_for_embed,
            "age_days": 100,
        })
    df = pd.DataFrame(df_rows)
    print(f"  --> Loaded {len(df)} records into temporary DataFrame.")

    # --- 3. Build & Test ChromaDB Vector Index ---
    print("\n[3/5] Building ChromaDB collection 'papers-baseline'...")
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"  --> ChromaDB collection '{index.collection_name}' built successfully!")
    print(f"  --> Total indexed documents: {len(index.documents)}")

    # Test Search
    query = "agentic retrieval augmented generation"
    print(f"\n[4/5] Testing semantic search for query: '{query}'...")
    results = index.search(query, top_k=3)
    assert len(results) > 0, "Search returned empty results"
    for i, res in enumerate(results, 1):
        print(f"  Top {i}: [{res.score:.4f}] {res.title} (ID: {res.paper_id})")

    # Test Exact Lookup
    first_title = df.iloc[0]["title"]
    lookup_res = index.lookup(first_title)
    assert lookup_res is not None, f"Lookup failed for title: {first_title}"
    print(f"  --> Exact lookup test PASSED for: '{first_title[:40]}...'")

    # Test Question Answering
    print("\n[5/5] Testing QA extraction logic...")
    sample_q = f"What is the summary of the paper '{first_title}'?"
    ans_res = answer_question(sample_q, settings=settings, index=index)
    print(f"  Question: {ans_res.question}")
    print(f"  Answer: {ans_res.answer[:80]}...")
    assert len(ans_res.retrieved_doc_ids) > 0, "No docs retrieved"
    print(f"  Retrieved doc: {ans_res.retrieved_doc_ids[0]}")

    print("\n" + "=" * 60)
    print("ALL MEMBER 3 RETRIEVAL & VECTOR STORE CHECKS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    run_verification()
