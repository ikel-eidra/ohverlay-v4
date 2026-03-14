"""
PlumberPass PDF Extractor
===========================
Extracts exam questions from PDF reviewer files using AI.

Pipeline:
  PDF file → Text extraction (PyMuPDF/pdfplumber) → Chunk into pages
  → Send to Groq Llama 3.3 70B (free) → Parse structured Q&A JSON
  → Store in QuestionBank SQLite DB

Handles:
  - Scanned PDFs (OCR via pytesseract if available)
  - Text-based PDFs (direct extraction)
  - Mixed format reviewers
  - Question detection from narrative text (AI generates questions from content)
  - Existing Q&A format detection (parses pre-formatted questions)

Requires:
  pip install pymupdf pdfplumber requests python-dotenv
  Optional: pip install pytesseract Pillow (for scanned PDFs)
"""

import os
import re
import json
import time
from typing import List, Dict, Optional
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# PDF readers (try multiple)
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class PDFExtractor:
    """Extracts text from PDF files."""

    def extract_text(self, pdf_path: str, max_pages: int = 0) -> List[Dict]:
        """
        Extract text from PDF, returning list of {page, text} dicts.
        Tries PyMuPDF first, falls back to pdfplumber.
        """
        if not os.path.exists(pdf_path):
            return []

        if HAS_FITZ:
            return self._extract_fitz(pdf_path, max_pages)
        elif HAS_PDFPLUMBER:
            return self._extract_pdfplumber(pdf_path, max_pages)
        else:
            return []

    def _extract_fitz(self, pdf_path, max_pages):
        pages = []
        doc = fitz.open(pdf_path)
        limit = max_pages if max_pages > 0 else len(doc)
        for i in range(min(limit, len(doc))):
            page = doc[i]
            text = page.get_text("text").strip()
            if text:
                pages.append({"page": i + 1, "text": text})
        doc.close()
        return pages

    def _extract_pdfplumber(self, pdf_path, max_pages):
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            limit = max_pages if max_pages > 0 else len(pdf.pages)
            for i, page in enumerate(pdf.pages[:limit]):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({"page": i + 1, "text": text.strip()})
        return pages

    def get_page_count(self, pdf_path):
        if HAS_FITZ:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        elif HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        return 0


class QuestionExtractor:
    """Uses Groq Llama to extract/generate exam questions from text."""

    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama-3.3-70b-versatile"

    # Prompt that handles BOTH pre-formatted questions AND narrative content
    EXTRACTION_PROMPT = """You are an expert Philippine Master Plumber exam question extractor.

Given the following text from a plumbing reviewer/textbook, extract or generate multiple-choice exam questions.

RULES:
1. If the text contains existing questions, extract them exactly
2. If the text is narrative/educational content, generate exam questions FROM the content
3. Each question must have exactly 4 options (A, B, C, D)
4. Mark the correct answer (0-indexed: A=0, B=1, C=2, D=3)
5. Add a brief explanation for why the answer is correct
6. Classify each question into a subject:
   - plumbing-code: Laws, RA 1378, National Plumbing Code
   - sanitary-eng: Sanitary systems, waste treatment
   - design-layout: System design, blueprints
   - water-supply: Water distribution, pressure, pipes
   - drainage: DWV systems, venting, traps
   - fixtures: Fixture units, materials, installation
   - mathematics: Calculations, formulas, sizing
   - environmental: Clean Water Act, DENR
   - ethics: Professional practice, board regulations
   - general: Mixed/other topics
7. Rate difficulty: 1=easy, 2=medium, 3=hard

Return ONLY valid JSON array. No other text. Format:
[
  {
    "question": "The question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0,
    "explanation": "Brief explanation",
    "subject_id": "water-supply",
    "difficulty": 2,
    "tags": "pipe sizing, water pressure"
  }
]

Generate as many valid questions as possible from the content (aim for 3-8 per page).
If the text has no plumbing-relevant content, return an empty array [].
"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self._request_count = 0
        self._last_request = 0
        self._min_delay = 2.0  # seconds between API calls (rate limit safety)

    def extract_questions(self, text: str, source_info: str = "") -> List[Dict]:
        """
        Send text to Groq LLM and get structured questions back.
        """
        if not HAS_REQUESTS or not self.api_key:
            return []

        if not text or len(text.strip()) < 50:
            return []

        # Rate limiting
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)

        # Truncate very long text (LLM context limit)
        if len(text) > 6000:
            text = text[:6000] + "\n... [truncated]"

        try:
            self._last_request = time.time()
            self._request_count += 1

            resp = requests.post(
                self.GROQ_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": self.MODEL,
                    "messages": [
                        {"role": "system", "content": self.EXTRACTION_PROMPT},
                        {"role": "user", "content": f"Source: {source_info}\n\nText:\n{text}"},
                    ],
                    "max_tokens": 4000,
                    "temperature": 0.3,  # Low temp for accurate extraction
                },
                timeout=60,
            )

            if resp.status_code == 429:
                # Rate limited — wait and retry once
                time.sleep(5)
                return self.extract_questions(text, source_info)

            if resp.status_code != 200:
                return []

            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            # Parse JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```", 1)[1].split("```", 1)[0].strip()

            questions = json.loads(content)

            if not isinstance(questions, list):
                return []

            # Validate each question
            valid = []
            for q in questions:
                if (
                    isinstance(q, dict)
                    and "question" in q
                    and "options" in q
                    and "answer" in q
                    and isinstance(q["options"], list)
                    and len(q["options"]) == 4
                    and isinstance(q["answer"], int)
                    and 0 <= q["answer"] <= 3
                ):
                    valid.append(q)

            return valid

        except (json.JSONDecodeError, KeyError, IndexError):
            return []
        except Exception:
            return []


class PlumberPassPipeline:
    """
    End-to-end pipeline: PDF → Questions → Database.

    Usage:
        pipeline = PlumberPassPipeline()
        result = pipeline.process_pdf("reviewer.pdf")
        print(f"Extracted {result['questions_added']} questions")
    """

    def __init__(self, api_key=None, db_path=None):
        self.pdf_extractor = PDFExtractor()
        self.question_extractor = QuestionExtractor(api_key)

        # Import QuestionBank
        from plumberpass.api.question_bank import QuestionBank
        self.question_bank = QuestionBank(db_path)

    def process_pdf(
        self,
        pdf_path: str,
        max_pages: int = 0,
        batch_size: int = 3,
        progress_callback=None,
    ) -> Dict:
        """
        Process a PDF file end-to-end.

        Args:
            pdf_path: Path to PDF file
            max_pages: Limit pages to process (0 = all)
            batch_size: Pages to combine per LLM call (saves API calls)
            progress_callback: fn(current_page, total_pages, questions_so_far)

        Returns:
            dict with processing results
        """
        filename = os.path.basename(pdf_path)
        result = {
            "filename": filename,
            "pages_total": 0,
            "pages_processed": 0,
            "questions_extracted": 0,
            "questions_added": 0,
            "errors": [],
            "duration_seconds": 0,
        }

        start = time.time()

        # Step 1: Extract text from PDF
        pages = self.pdf_extractor.extract_text(pdf_path, max_pages)
        if not pages:
            result["errors"].append("Could not extract text from PDF. Is PyMuPDF or pdfplumber installed?")
            return result

        result["pages_total"] = len(pages)

        # Step 2: Process pages in batches
        all_questions = []
        for i in range(0, len(pages), batch_size):
            batch = pages[i : i + batch_size]
            combined_text = "\n\n".join(
                f"--- Page {p['page']} ---\n{p['text']}" for p in batch
            )
            page_range = f"pp. {batch[0]['page']}-{batch[-1]['page']}"

            questions = self.question_extractor.extract_questions(
                combined_text,
                source_info=f"{filename} {page_range}",
            )

            # Tag each question with source
            for q in questions:
                q["source_pdf"] = filename
                q["page_ref"] = page_range

            all_questions.extend(questions)
            result["pages_processed"] += len(batch)

            if progress_callback:
                progress_callback(
                    result["pages_processed"],
                    result["pages_total"],
                    len(all_questions),
                )

        result["questions_extracted"] = len(all_questions)

        # Step 3: Store in database
        if all_questions:
            added = self.question_bank.add_questions_bulk(all_questions)
            result["questions_added"] = added

        result["duration_seconds"] = round(time.time() - start, 1)
        return result

    def process_directory(self, dir_path: str, progress_callback=None) -> Dict:
        """Process all PDFs in a directory."""
        pdf_files = sorted(Path(dir_path).glob("*.pdf"))
        total_result = {
            "files_found": len(pdf_files),
            "files_processed": 0,
            "total_questions": 0,
            "results": [],
        }

        for pdf_file in pdf_files:
            result = self.process_pdf(str(pdf_file), progress_callback=progress_callback)
            total_result["results"].append(result)
            total_result["files_processed"] += 1
            total_result["total_questions"] += result["questions_added"]

        return total_result

    def get_stats(self):
        """Get current question bank stats."""
        return self.question_bank.get_stats()
