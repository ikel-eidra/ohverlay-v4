"""
PlumberPass - Philippine Master Plumber Exam Reviewer
======================================================
Connected to Ohverlay as an overlay exam reviewer.

Architecture:
  plumberpass/
    api/
      server.py         - FastAPI endpoints for question bank
      question_bank.py  - SQLite question database
    pipeline/
      pdf_extractor.py  - Extract Q&A from PDF reviewers using Groq LLM
      rag_builder.py    - Build RAG index from plumbing documents
    data/
      plumberpass.db    - SQLite question bank
      pdfs/             - Source PDF reviewer files

Exam Coverage (Philippine Master Plumber Licensure):
  - Plumbing Code of the Philippines (RA 1378)
  - National Plumbing Code
  - Sanitary Engineering
  - Plumbing Design & Layout
  - Water Supply Systems
  - Drainage & Sewage Systems
  - Plumbing Fixtures & Materials
  - Plumbing Mathematics
  - Environmental Laws
  - Professional Ethics & Practice
"""

PLUMBERPASS_VERSION = "1.0.0"
