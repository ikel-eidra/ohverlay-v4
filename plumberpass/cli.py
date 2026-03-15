#!/usr/bin/env python3
"""
PlumberPass CLI - Process PDFs and manage question bank.

Usage:
  python -m plumberpass process reviewer.pdf        # Extract questions from one PDF
  python -m plumberpass process ./pdfs/              # Process all PDFs in folder
  python -m plumberpass stats                        # Show study stats
  python -m plumberpass subjects                     # List subjects
  python -m plumberpass count                        # Total questions
  python -m plumberpass quiz                         # Quick terminal quiz
  python -m plumberpass serve                        # Start API server
  python -m plumberpass export questions.json        # Export all questions
"""

import sys
import os
import json
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plumberpass.api.question_bank import QuestionBank
from plumberpass.pipeline.pdf_extractor import PlumberPassPipeline


def cmd_process(args):
    """Process PDF file(s) and extract questions."""
    pipeline = PlumberPassPipeline()
    path = args.input

    def progress(current, total, questions):
        pct = int(current / max(total, 1) * 100)
        print(f"\r  [{pct:3d}%] Page {current}/{total} | {questions} questions extracted", end="", flush=True)

    if os.path.isdir(path):
        print(f"Processing all PDFs in: {path}")
        result = pipeline.process_directory(path, progress_callback=progress)
        print(f"\n\nDone!")
        print(f"  Files processed: {result['files_processed']}/{result['files_found']}")
        print(f"  Total questions added: {result['total_questions']}")
        for r in result["results"]:
            status = "OK" if not r["errors"] else "ERRORS"
            print(f"    {r['filename']}: {r['questions_added']} questions [{status}]")
    elif os.path.isfile(path):
        print(f"Processing: {path}")
        result = pipeline.process_pdf(path, progress_callback=progress)
        print(f"\n\nDone in {result['duration_seconds']}s!")
        print(f"  Pages: {result['pages_processed']}/{result['pages_total']}")
        print(f"  Questions extracted: {result['questions_extracted']}")
        print(f"  Questions added to bank: {result['questions_added']}")
        if result["errors"]:
            for err in result["errors"]:
                print(f"  Error: {err}")
    else:
        print(f"Not found: {path}")
        return 1

    # Show total
    stats = pipeline.get_stats()
    print(f"\nQuestion bank total: {stats['total_questions']} questions")


def cmd_stats(args):
    """Show study statistics."""
    bank = QuestionBank()
    stats = bank.get_stats()

    print("PlumberPass Study Stats")
    print("=" * 50)
    print(f"Total questions:  {stats['total_questions']}")
    print(f"Unique answered:  {stats['unique_answered']}")
    print(f"Coverage:         {stats['coverage']}%")
    print(f"Total attempts:   {stats['total_attempts']}")
    print(f"Accuracy:         {stats['accuracy']}%")
    print()
    print("By Subject:")
    print("-" * 50)
    for s in stats["subjects"]:
        if s["total"] > 0:
            acc = round(s["correct"] / max(s["answered"], 1) * 100) if s["answered"] else 0
            bar = "#" * int(acc / 5) + "." * (20 - int(acc / 5))
            print(f"  {s['name'][:28]:<30} {s['total']:>4} q | {acc:>3}% [{bar}]")


def cmd_subjects(args):
    bank = QuestionBank()
    for s in bank.get_subjects():
        print(f"  {s['id']:<18} {s['name']:<35} ({s['question_count']} questions)")


def cmd_count(args):
    bank = QuestionBank()
    print(f"Total questions: {bank.get_total_questions()}")


def cmd_quiz(args):
    """Quick terminal quiz mode."""
    bank = QuestionBank()
    total = bank.get_total_questions()
    if total == 0:
        print("No questions in bank. Process some PDFs first:")
        print("  python -m plumberpass process reviewer.pdf")
        return

    print(f"PlumberPass Quick Quiz ({total} questions available)")
    print("Type 'q' to quit\n")

    score = 0
    asked = 0
    letters = "ABCD"

    while True:
        q = bank.get_random_question()
        if not q:
            break

        asked += 1
        print(f"\n--- Question {asked} [{q.get('subject_id', 'general')}] ---")
        print(f"  {q['question']}\n")

        for i, opt in enumerate(q["options"]):
            print(f"  {letters[i]}. {opt}")

        ans = input(f"\nYour answer (A-D): ").strip().upper()
        if ans == "Q":
            break

        idx = "ABCD".find(ans)
        if idx == q["answer"]:
            score += 1
            print(f"  Correct!")
        else:
            print(f"  Wrong. Answer: {letters[q['answer']]}. {q['options'][q['answer']]}")

        if q.get("explanation"):
            print(f"  Explanation: {q['explanation']}")

        bank.record_answer(q["id"], idx == q["answer"])

    if asked > 0:
        print(f"\nScore: {score}/{asked} ({round(score/asked*100)}%)")


def cmd_export(args):
    """Export all questions to JSON."""
    bank = QuestionBank()
    questions = bank.get_questions_for_overlay(count=9999, smart=False)
    output = args.output or "plumberpass-questions.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(questions)} questions to {output}")


def cmd_serve(args):
    """Start the PlumberPass API server."""
    try:
        import uvicorn
        port = args.port or 8401
        print(f"Starting PlumberPass API on port {port}...")
        uvicorn.run("plumberpass.api.server:app", host="0.0.0.0", port=port, reload=True)
    except ImportError:
        print("Install uvicorn: pip install uvicorn[standard] fastapi")


def main():
    parser = argparse.ArgumentParser(
        description="PlumberPass - Philippine Master Plumber Exam Reviewer",
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("process", help="Extract questions from PDF(s)")
    p.add_argument("input", help="PDF file or directory of PDFs")

    sub.add_parser("stats", help="Show study statistics")
    sub.add_parser("subjects", help="List exam subjects")
    sub.add_parser("count", help="Count total questions")
    sub.add_parser("quiz", help="Quick terminal quiz")

    p = sub.add_parser("export", help="Export questions to JSON")
    p.add_argument("output", nargs="?", default="plumberpass-questions.json")

    p = sub.add_parser("serve", help="Start API server")
    p.add_argument("--port", type=int, default=8401)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    cmds = {
        "process": cmd_process,
        "stats": cmd_stats,
        "subjects": cmd_subjects,
        "count": cmd_count,
        "quiz": cmd_quiz,
        "export": cmd_export,
        "serve": cmd_serve,
    }
    cmds[args.command](args)


if __name__ == "__main__":
    main()
